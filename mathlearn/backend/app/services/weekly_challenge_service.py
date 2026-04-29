from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.models.weekly_challenge import WeeklyChallengeEntry, WeeklyRewardTier, ClaimedReward
from app.models.user import User


class WeeklyChallengeService:
    """Сервис для управления недельными челленджами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_week_range(self) -> tuple[datetime, datetime]:
        """Получить диапазон текущей недели (понедельник 00:00 - воскресенье 23:59)"""
        now = datetime.utcnow()
        # Находим последний понедельник
        days_since_monday = now.weekday()
        last_monday = now - timedelta(days=days_since_monday)
        week_start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        return week_start, week_end
    
    def get_or_create_current_entry(self, user_id: int) -> WeeklyChallengeEntry:
        """Получить или создать запись недельного челленджа для пользователя"""
        week_start, week_end = self.get_current_week_range()
        
        entry = self.db.query(WeeklyChallengeEntry).filter(
            WeeklyChallengeEntry.user_id == user_id,
            WeeklyChallengeEntry.week_start == week_start
        ).first()
        
        if not entry:
            # Создаем новую запись для текущей недели
            entry = WeeklyChallengeEntry(
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                current_points=0,
                target_points=1000  # Можно настроить динамически
            )
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
        
        return entry
    
    def get_current_entry(self, user_id: int) -> Optional[WeeklyChallengeEntry]:
        """Получить текущую запись недельного челленджа"""
        week_start, _ = self.get_current_week_range()
        return self.db.query(WeeklyChallengeEntry).filter(
            WeeklyChallengeEntry.user_id == user_id,
            WeeklyChallengeEntry.week_start == week_start
        ).first()
    
    def get_user_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить статус недельного челленджа пользователя"""
        entry = self.get_current_entry(user_id)
        if not entry:
            entry = self.get_or_create_current_entry(user_id)
        
        # Получаем список полученных наград
        claimed_rewards = self.db.query(ClaimedReward).filter(
            ClaimedReward.entry_id == entry.id
        ).all()
        completed_tiers = [cr.reward_tier_id for cr in claimed_rewards]
        
        return {
            "current_points": entry.current_points,
            "target_points": entry.target_points,
            "week_start": entry.week_start,
            "week_end": entry.week_end,
            "completed_tiers": completed_tiers,
            "is_active": True
        }
    
    def add_points(self, user_id: int, points: int) -> WeeklyChallengeEntry:
        """Добавить очки пользователю в текущем челлендже"""
        entry = self.get_or_create_current_entry(user_id)
        entry.current_points += points
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_all_reward_tiers(self) -> List[WeeklyRewardTier]:
        """Получить все уровни наград"""
        return self.db.query(WeeklyRewardTier).order_by(WeeklyRewardTier.required_points).all()
    
    def is_reward_claimed(self, entry_id: int, reward_tier_id: int) -> bool:
        """Проверить, была ли награда уже получена"""
        claimed = self.db.query(ClaimedReward).filter(
            ClaimedReward.entry_id == entry_id,
            ClaimedReward.reward_tier_id == reward_tier_id
        ).first()
        return claimed is not None
    
    def claim_reward(self, entry_id: int, reward_tier_id: int, user_id: int) -> ClaimedReward:
        """Записать получение награды пользователем"""
        # Получаем информацию о награде
        reward_tier = self.db.query(WeeklyRewardTier).filter(
            WeeklyRewardTier.id == reward_tier_id
        ).first()
        
        if not reward_tier:
            raise ValueError("Награда не найдена")
        
        # Создаем запись о полученной награде
        claimed_reward = ClaimedReward(
            entry_id=entry_id,
            reward_tier_id=reward_tier_id,
            reward_type=reward_tier.reward_type,
            reward_value=reward_tier.reward_value
        )
        self.db.add(claimed_reward)
        
        # Применяем награду к пользователю
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            if reward_tier.reward_type == "xp":
                user.total_xp += reward_tier.reward_value
            elif reward_tier.reward_type == "coins":
                user.coins += reward_tier.reward_value
            elif reward_tier.reward_type == "freeze":
                user.streak_freeze_count += reward_tier.reward_value
        
        self.db.commit()
        self.db.refresh(claimed_reward)
        return claimed_reward
