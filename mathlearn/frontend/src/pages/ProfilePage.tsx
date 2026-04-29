import React, { useState, useEffect } from 'react';
import { profileApi, type UserProfile, type ModeConfig } from '../api/profile';
import LearningModeSelector, { type LearningMode } from '../components/LearningModeSelector';
import ModeCard, { type ModeInfo } from '../components/ModeCard';
import './ProfilePage.css';

const MODES: ModeInfo[] = [
  {
    mode: 'classic',
    title: 'Классический',
    description: 'Изучение таблиц умножения по порядку с прогрессом',
    icon: '🗺️',
    is_pro: false,
    primary_metric: 'Прогресс групп'
  },
  {
    mode: 'sprinter',
    title: 'Спринтер',
    description: 'Быстрые сессии на скорость реакции',
    icon: '⚡',
    is_pro: false,
    primary_metric: 'Среднее время ответа'
  },
  {
    mode: 'weak_spots',
    title: 'Работа над ошибками',
    description: 'Тренировка слабых мест и проблемных примеров',
    icon: '🧠',
    is_pro: false,
    primary_metric: 'Уменьшение ошибок'
  },
  {
    mode: 'streak_hunter',
    title: 'Охотник за сериями',
    description: 'Поддержание ежедневной серии побед',
    icon: '🔥',
    is_pro: false,
    primary_metric: 'Текущая серия'
  },
  {
    mode: 'fighter',
    title: 'Боец',
    description: 'Ежедневные вызовы и лидерборды',
    icon: '🎮',
    is_pro: true,
    primary_metric: 'Очки рейтинга'
  },
  {
    mode: 'zen',
    title: 'Дзен',
    description: 'Спокойное обучение без таймера и давления',
    icon: '🌙',
    is_pro: true,
    primary_metric: 'Точность'
  }
];

const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [modeConfig, setModeConfig] = useState<ModeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [pendingMode, setPendingMode] = useState<string | null>(null);
  const [showWarning, setShowWarning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await profileApi.getProfile();
      setProfile(data.profile);
      setModeConfig(data.mode_config);
      setError(null);
    } catch (err) {
      console.error('Failed to load profile:', err);
      setError('Не удалось загрузить профиль. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleModeClick = (mode: string) => {
    if (mode !== modeConfig?.mode) {
      setPendingMode(mode);
      setShowWarning(true);
    }
  };

  const confirmModeChange = async () => {
    if (!pendingMode) return;
    
    try {
      const data = await profileApi.updateMode(pendingMode as LearningMode);
      setProfile(data.profile);
      setModeConfig(data.mode_config);
      setShowModeSelector(false);
      setShowWarning(false);
      setPendingMode(null);
    } catch (err) {
      console.error('Failed to update mode:', err);
      setError('Не удалось изменить режим обучения. Попробуйте позже.');
      setShowWarning(false);
      setPendingMode(null);
    }
  };

  const cancelModeChange = () => {
    setShowWarning(false);
    setPendingMode(null);
  };

  if (loading) {
    return <div className="profile-loading">Загрузка профиля...</div>;
  }

  if (error) {
    return (
      <div className="profile-error">
        <p>{error}</p>
        <button onClick={loadProfile}>Попробовать снова</button>
      </div>
    );
  }

  if (!profile || !modeConfig) {
    return <div className="profile-loading">Профиль не найден</div>;
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>Профиль пользователя</h1>
        <div className="user-info">
          <div className="avatar-placeholder">{profile.username.charAt(0).toUpperCase()}</div>
          <div className="user-details">
            <h2>{profile.username}</h2>
            <p>{profile.email}</p>
          </div>
        </div>
      </div>

      <div className="profile-stats">
        <div className="stat-card">
          <div className="stat-icon">🔥</div>
          <div className="stat-value">{profile.current_streak}</div>
          <div className="stat-label">Текущая серия</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🏆</div>
          <div className="stat-value">{profile.best_streak}</div>
          <div className="stat-label">Лучшая серия</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">❄️</div>
          <div className="stat-value">{profile.streak_freeze_count}</div>
          <div className="stat-label">Заморозки</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-value">x{profile.xp_multiplier.toFixed(1)}</div>
          <div className="stat-label">Множитель XP</div>
        </div>
      </div>

      <div className="current-mode-section">
        <div className="mode-info-card">
          <h3>Текущий режим обучения</h3>
          <div className="mode-display" style={{ borderColor: getModeColor(modeConfig.mode) }}>
            <div className="mode-emoji">{getModeEmoji(modeConfig.mode)}</div>
            <div className="mode-details">
              <h4>{modeConfig.title}</h4>
              <p>{modeConfig.description}</p>
              <div className="mode-features">
                {modeConfig.has_timer && <span className="feature-badge">⏱️ Таймер</span>}
                {modeConfig.unlimited_hints && <span className="feature-badge">♾️ Бесконечные подсказки</span>}
                {modeConfig.preserves_streak && <span className="feature-badge">🛡️ Сохраняет серию</span>}
              </div>
            </div>
          </div>
          <button 
            className="change-mode-btn"
            onClick={() => setShowModeSelector(true)}
          >
            Изменить режим
          </button>
        </div>
      </div>

      {showModeSelector && (
        <div className="mode-selector-overlay">
          <div className="mode-selector-modal">
            <button className="close-btn" onClick={() => setShowModeSelector(false)}>✕</button>
            <h2>Выберите режим обучения</h2>
            <div className="modes-grid">
              {MODES.map((mode) => (
                <ModeCard
                  key={mode.mode}
                  mode={mode}
                  selected={modeConfig?.mode === mode.mode}
                  onSelect={handleModeClick}
                  isProUser={profile?.is_pro ?? false}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {showWarning && (
        <div className="warning-overlay">
          <div className="warning-modal">
            <h3>⚠️ Внимание</h3>
            <p>Некоторые настройки сессии будут сброшены</p>
            <div className="warning-actions">
              <button className="btn-cancel" onClick={cancelModeChange}>Отмена</button>
              <button className="btn-confirm" onClick={confirmModeChange}>Продолжить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function getModeColor(mode: string): string {
  const colors: Record<string, string> = {
    classic: '#4facfe',
    sprinter: '#f093fb',
    weak_spots: '#fa709a',
    streak_hunter: '#ff9a9e',
    fighter: '#a18cd1',
    zen: '#84fab0'
  };
  return colors[mode] || '#cccccc';
}

function getModeEmoji(mode: string): string {
  const emojis: Record<string, string> = {
    classic: '🗺️',
    sprinter: '⚡',
    weak_spots: '🧠',
    streak_hunter: '🔥',
    fighter: '🎮',
    zen: '🌙'
  };
  return emojis[mode] || '❓';
}

export default ProfilePage;
