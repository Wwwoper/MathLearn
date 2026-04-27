import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { statsApi } from '../api/stats';
import apiClient from '../api/client';
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

const HomePage = () => {
  const [streak, setStreak] = useState({ current_streak: 0, max_streak: 0 });
  const [todayStats, setTodayStats] = useState<TodayStats>({ due_count: 0, completed_today: 0 });
  const [progressPercent, setProgressPercent] = useState(0);
  const [aiRecommendation, setAiRecommendation] = useState<AIRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHomeData = async () => {
      try {
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
      } catch (error) {
        console.error('Error fetching home data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  if (loading) {
    return <div className="home-loading">Загрузка...</div>;
  }

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

      {/* Карточка "Повторить сегодня" */}
      <div className="home-section">
        <div className="review-card">
          <h2 className="card-title">📚 Повторить сегодня</h2>
          <div className="review-stats">
            <span className="review-count">{todayStats.due_count}</span>
            <span className="review-label">карточек ожидают повторения</span>
          </div>
          {todayStats.due_count > 0 ? (
            <Link to="/learn" className="start-button">
              Начать повторение
            </Link>
          ) : (
            <div className="all-done">
              <span className="check-icon">✅</span>
              <span>Отлично! На сегодня всё выполнено!</span>
            </div>
          )}
          {todayStats.completed_today > 0 && (
            <p className="completed-info">
              Уже выполнено: {todayStats.completed_today} карточек
            </p>
          )}
        </div>
      </div>

      {/* Мини-таблица прогресса */}
      <div className="home-section">
        <div className="progress-card">
          <h2 className="card-title">📊 Прогресс освоения</h2>
          <div className="progress-bar-container">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
          <div className="progress-percent">{progressPercent}%</div>
          <p className="progress-description">
            Таблицы умножения изучено ({progressPercent}% карточек с mastery &gt; 2.0)
          </p>
          <Link to="/table" className="view-table-link">
            Показать таблицу →
          </Link>
        </div>
      </div>

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
