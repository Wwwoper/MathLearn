import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { statsApi } from '../api/stats';
import apiClient from '../api/client';
import { profileApi } from '../api/profile';
import { useAuthStore } from '../store/useAuthStore';
import type { LearningMode } from '../components/LearningModeSelector/LearningModeSelector';
import './HomePage.css';

interface SRProgress {
  matrix: Array<Array<{
    factor_a: number;
    factor_b: number;
    ease_factor: number | null;
    interval_days: number | null;
    repetitions: number | null;
    lapses: number | null;
    next_review_at: string | null;
  }>>;
}

interface TodayStats {
  due_count: number;
  completed_today: number;
}

interface AIRecommendation {
  id: number;
  lesson_plan: Array<{
    day: number;
    focus_facts: string[];
    mode: string;
    explanation: string;
  }>;
  reasoning: string;
  model_name: string;
  generated_at: string;
}

interface WeakSpotsData {
  weak_facts: Array<{ a: number; b: number; error_rate: number }>;
}

interface SprinterStats {
  avg_response_ms: number;
  last_7_days: Array<{ date: string; avg_ms: number }>;
}

interface StreakHunterProgress {
  current_session: number;
  session_target: number;
}

interface FighterChallenge {
  id: number;
  condition_type: string;
  target_value: number;
  progress: number;
  reward_xp: number;
}

const HomePage = () => {
  const { user, updateUserLearningMode } = useAuthStore();
  const [streak, setStreak] = useState({ current_streak: 0, max_streak: 0 });
  const [todayStats, setTodayStats] = useState<TodayStats>({ due_count: 0, completed_today: 0 });
  const [progressPercent, setProgressPercent] = useState(0);
  const [aiRecommendation, setAiRecommendation] = useState<AIRecommendation | null>(null);
  const [learningMode, setLearningMode] = useState<LearningMode>('classic');
  const [weakSpots, setWeakSpots] = useState<WeakSpotsData | null>(null);
  const [sprinterStats, setSprinterStats] = useState<SprinterStats | null>(null);
  const [streakHunterProgress, setStreakHunterProgress] = useState<StreakHunterProgress | null>(null);
  const [fighterChallenge, setFighterChallenge] = useState<FighterChallenge | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        // Загружаем профиль для получения режима обучения
        const profileRes = await profileApi.getProfile();
        const mode = profileRes.profile.learning_mode || 'classic';
        setLearningMode(mode);
        if (user && mode !== user.learning_mode) {
          updateUserLearningMode(mode);
        }

        const [streakRes, todayRes, progressRes, aiRes] = await Promise.all([
          statsApi.getStreak(),
          apiClient.get<TodayStats>('/sr/today'),
          apiClient.get<SRProgress>('/sr/progress'),
          apiClient.get<AIRecommendation | null>('/ai/recommendation').catch(() => ({ data: null })),
        ]);

        setStreak(streakRes);
        setTodayStats(todayRes.data);

        // Вычисление процента освоения (карточки с ease_factor > 2.0)
        const matrix = progressRes.data.matrix;
        let masteredCount = 0;
        let totalCount = 0;
        for (const row of matrix) {
          for (const cell of row) {
            totalCount++;
            if (cell.ease_factor !== null && cell.ease_factor > 2.0) {
              masteredCount++;
            }
          }
        }
        setProgressPercent(totalCount > 0 ? Math.round((masteredCount / totalCount) * 100) : 0);

        if (aiRes.data) {
          setAiRecommendation(aiRes.data);
        }

        // Загружаем данные в зависимости от режима
        await fetchModeSpecificData(mode);
      } catch (error) {
        console.error('Error fetching home data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  const fetchModeSpecificData = async (mode: LearningMode) => {
    try {
      switch (mode) {
        case 'weak_spots':
          const weakRes = await apiClient.get<WeakSpotsData>('/sr/weak-spots');
          setWeakSpots(weakRes.data);
          break;
        case 'sprinter':
          const sprinterRes = await apiClient.get<SprinterStats>('/sr/sprinter-stats');
          setSprinterStats(sprinterRes.data);
          break;
        case 'streak_hunter':
          const streakRes = await apiClient.get<StreakHunterProgress>('/sr/streak-hunter-progress');
          setStreakHunterProgress(streakRes.data);
          break;
        case 'fighter':
          const fighterRes = await apiClient.get<FighterChallenge>('/sr/daily-challenge');
          setFighterChallenge(fighterRes.data);
          break;
        default:
          break;
      }
    } catch (error) {
      console.error(`Error fetching ${mode} data:`, error);
    }
  };

  if (loading) {
    return <div className="home-loading">Загрузка...</div>;
  }

  // Рендер виджетов в зависимости от режима обучения
  const renderModeSpecificWidgets = () => {
    switch (learningMode) {
      case 'classic':
        return (
          <div className="home-section">
            <div className="mode-widget-card classic-widget">
              <h2 className="card-title">📊 Прогресс по таблицам</h2>
              <div className="progress-bar-container">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${progressPercent}%` }}
                ></div>
              </div>
              <div className="progress-percent">{progressPercent}%</div>
              <p className="widget-description">
                Групп с mastery ≥ 2.0: {progressPercent}%
              </p>
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">📚 Карточки в очереди</h2>
              <div className="widget-stat-large">{todayStats.due_count}</div>
              <p className="widget-description">карточек ожидают повторения сегодня</p>
            </div>
          </div>
        );

      case 'sprinter':
        return (
          <div className="home-section">
            <div className="mode-widget-card sprinter-widget">
              <h2 className="card-title">⚡ Средняя скорость ответа</h2>
              <div className="widget-stat-large">
                {sprinterStats ? `${Math.round(sprinterStats.avg_response_ms)} мс` : '--'}
              </div>
              <p className="widget-description">за последние 7 дней</p>
              {sprinterStats && sprinterStats.last_7_days.length > 0 && (
                <div className="mini-chart">
                  {sprinterStats.last_7_days.map((day, idx) => (
                    <div key={idx} className="chart-bar" style={{ height: `${Math.min(day.avg_ms / 10, 100)}%` }}>
                      <span className="chart-label">{day.avg_ms}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">📋 Карточки в очереди</h2>
              <div className="widget-stat-large">{todayStats.due_count}</div>
            </div>
          </div>
        );

      case 'weak_spots':
        return (
          <div className="home-section">
            <div className="mode-widget-card weak-spots-widget">
              <h2 className="card-title">🧠 Слабые места</h2>
              <div className="weak-spots-grid">
                {weakSpots && weakSpots.weak_facts.slice(0, 10).map((fact, idx) => (
                  <div key={idx} className="weak-spot-cell" style={{ backgroundColor: `rgba(255, 0, 0, ${fact.error_rate})` }}>
                    {fact.a}×{fact.b}
                  </div>
                ))}
              </div>
              <p className="widget-description">Топ-10 примеров с наибольшим количеством ошибок</p>
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">🔴 Топ-3 слабые карточки</h2>
              {weakSpots && weakSpots.weak_facts.slice(0, 3).map((fact, idx) => (
                <div key={idx} className="weak-fact-item">
                  <span className="fact-expression">{fact.a} × {fact.b}</span>
                  <span className="fact-error-rate">{Math.round(fact.error_rate * 100)}% ошибок</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'streak_hunter':
        return (
          <div className="home-section">
            <div className="mode-widget-card streak-hunter-widget">
              <h2 className="card-title">🔥 Серия побед</h2>
              <div className="streak-display-large">
                <span className="fire-icon-big">🔥</span>
                <span className="streak-count-big">{streak.current_streak}</span>
              </div>
              <p className="widget-description">дней подряд</p>
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">📊 Прогресс мини-сессии</h2>
              <div className="session-progress">
                <span className="session-count">
                  {streakHunterProgress ? `${streakHunterProgress.current_session}/${streakHunterProgress.session_target}` : '0/5'}
                </span>
                <div className="session-progress-bar">
                  <div 
                    className="session-progress-fill" 
                    style={{ width: streakHunterProgress ? `${(streakHunterProgress.current_session / streakHunterProgress.session_target) * 100}%` : '0%' }}
                  ></div>
                </div>
              </div>
              <p className="widget-description">карточек в текущей сессии</p>
            </div>
          </div>
        );

      case 'fighter':
        return (
          <div className="home-section">
            <div className="mode-widget-card fighter-widget">
              <h2 className="card-title">🎮 Ежедневный вызов</h2>
              {fighterChallenge ? (
                <>
                  <div className="challenge-condition">
                    <span className="condition-type">{fighterChallenge.condition_type === 'speed_improvement' ? '⚡ Улучшение скорости' : '🎯 Точность'}</span>
                    <span className="condition-target">Цель: {fighterChallenge.target_value}</span>
                  </div>
                  <div className="challenge-progress">
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill challenge-fill" 
                        style={{ width: `${Math.min((fighterChallenge.progress / fighterChallenge.target_value) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <span className="progress-text">{fighterChallenge.progress} / {fighterChallenge.target_value}</span>
                  </div>
                  <div className="challenge-reward">
                    🏆 Награда: {fighterChallenge.reward_xp} XP
                  </div>
                  <Link to="/drill" className="start-button challenge-start-btn">
                    Принять вызов
                  </Link>
                </>
              ) : (
                <p>Вызов ещё не сгенерирован</p>
              )}
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">🏆 Лидерборд</h2>
              <Link to="/leaderboard" className="leaderboard-link">
                Посмотреть рейтинг →
              </Link>
            </div>
          </div>
        );

      case 'zen':
        return (
          <div className="home-section">
            <div className="mode-widget-card zen-widget">
              <h2 className="card-title">🌙 Точность за 30 дней</h2>
              <div className="zen-accuracy-display">
                <span className="accuracy-percent">--%</span>
                <p className="accuracy-description">Статистика точности</p>
              </div>
            </div>
            <div className="mode-widget-card secondary-widget">
              <h2 className="card-title">💡 Карточки с подсказками</h2>
              <div className="widget-stat-large">{todayStats.due_count}</div>
              <p className="widget-description">карточек доступны с подсказками</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="home-page">
      <h1 className="home-title">Добро пожаловать в MathLearn!</h1>

      {/* Карточка "Учить таблицу" с выделением */}
      <div className="home-section">
        <Link to="/learn" className="start-button learn-table-card">
          <span className="fire-badge">🔥</span>
          <span className="card-title-text">Учить таблицу умножения</span>
          <span className="pulse-dot"></span>
        </Link>
      </div>

      {/* Streak Counter с анимацией */}
      <div className="home-section">
        <div className="streak-counter">
          <span className="fire-icon">🔥</span>
          <div className="streak-info">
            <span className="streak-count">{streak.current_streak}</span>
            <span className="streak-label">дней подряд</span>
          </div>
        </div>
      </div>

      {/* Виджеты в зависимости от режима обучения */}
      {renderModeSpecificWidgets()}

      {/* Блок с рекомендацией от ИИ */}
      {aiRecommendation && (
        <div className="home-section">
          <div className="ai-recommendation-card">
            <div className="ai-header">
              <span className="ai-icon">🤖</span>
              <h2 className="card-title">Рекомендация ИИ-тьютора</h2>
            </div>
            <p className="ai-reasoning">{aiRecommendation.reasoning}</p>
            <div className="ai-plan">
              <h3>План на ближайшие дни:</h3>
              {aiRecommendation.lesson_plan.slice(0, 3).map((day, index) => (
                <div key={index} className="ai-day-card">
                  <span className="day-badge">День {day.day}</span>
                  <p className="day-focus">
                    <strong>Фокус:</strong> {day.focus_facts.join(', ')}
                  </p>
                  <p className="day-mode">
                    <strong>Режим:</strong> {day.mode}
                  </p>
                  <p className="day-explanation">{day.explanation}</p>
                </div>
              ))}
            </div>
            <div className="ai-footer">
              <span className="generated-at">
                Сгенерировано: {new Date(aiRecommendation.generated_at).toLocaleDateString('ru-RU')}
              </span>
              <span className="model-name">Модель: {aiRecommendation.model_name}</span>
            </div>
            <Link to="/ai-tutor" className="ai-more-link">
              Подробнее →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
