import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import './TablePage.css';

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

interface TableProgress {
  table: number;
  mastered: number;
  total: number;
  percent: number;
  status: 'new' | 'learning' | 'mastered' | 'review';
}

interface CardStatus {
  new: number;
  learning: number;
  mastered: number;
  review: number;
}

const TablePage = () => {
  const [progress, setProgress] = useState<SRProgress | null>(null);
  const [tableProgresses, setTableProgresses] = useState<TableProgress[]>([]);
  const [cardStatuses, setCardStatuses] = useState<CardStatus>({ new: 0, learning: 0, mastered: 0, review: 0 });
  const [overallPercent, setOverallPercent] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const response = await apiClient.get<SRProgress>('/sr/progress');
        const data = response.data;
        setProgress(data);

        // Вычисление прогресса по каждой таблице
        const tables: TableProgress[] = [];
        let totalMastered = 0;
        let totalCount = 0;
        let newCount = 0;
        let learningCount = 0;
        let masteredCount = 0;
        let reviewCount = 0;

        for (let i = 0; i < 10; i++) {
          const row = data.matrix[i];
          let tableMastered = 0;
          let tableTotal = row.length;

          for (const cell of row) {
            totalCount++;
            const ef = cell.ease_factor ?? 0;
            const reps = cell.repetitions ?? 0;

            if (ef > 2.0) {
              tableMastered++;
              masteredCount++;
              totalMastered++;
            } else if (ef >= 1.3 && ef <= 2.0) {
              learningCount++;
            } else if (reps === 0) {
              newCount++;
            } else {
              reviewCount++;
            }
          }

          const percent = tableTotal > 0 ? Math.round((tableMastered / tableTotal) * 100) : 0;
          let status: TableProgress['status'] = 'new';
          if (percent === 100) status = 'mastered';
          else if (percent >= 80) status = 'mastered';
          else if (percent >= 50) status = 'learning';
          else if (percent > 0) status = 'review';

          tables.push({
            table: i + 1,
            mastered: tableMastered,
            total: tableTotal,
            percent,
            status,
          });
        }

        setTableProgresses(tables);
        setOverallPercent(totalCount > 0 ? Math.round((totalMastered / totalCount) * 100) : 0);
        setCardStatuses({ new: newCount, learning: learningCount, mastered: masteredCount, review: reviewCount });
      } catch (error) {
        console.error('Error fetching progress:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  const getStatusEmoji = (status: TableProgress['status']) => {
    switch (status) {
      case 'mastered': return '🟢';
      case 'learning': return '🟡';
      case 'review': return '🔴';
      case 'new': return '⚪';
      default: return '⚪';
    }
  };

  const getStatusText = (status: TableProgress['status']) => {
    switch (status) {
      case 'mastered': return 'Освоено';
      case 'learning': return 'Изучается';
      case 'review': return 'Повторить';
      case 'new': return 'Новая';
      default: return '';
    }
  };

  const getProgressBarColor = (percent: number) => {
    if (percent >= 80) return '#4CAF50';
    if (percent >= 50) return '#FFC107';
    if (percent > 0) return '#F44336';
    return '#E0E0E0';
  };

  if (loading) {
    return <div className="table-loading">Загрузка...</div>;
  }

  return (
    <div className="table-page">
      <h1 className="table-title">📊 Прогресс освоения</h1>

      {/* Общий прогресс */}
      <div className="overall-progress-card">
        <h2 className="card-subtitle">Общий прогресс</h2>
        <div className="overall-percent-circle">
          <svg className="progress-ring" width="200" height="200">
            <circle
              className="progress-ring-bg"
              strokeWidth="12"
              stroke="#E0E0E0"
              fill="transparent"
              r="80"
              cx="100"
              cy="100"
            />
            <circle
              className="progress-ring-fill"
              strokeWidth="12"
              stroke={getProgressBarColor(overallPercent)}
              fill="transparent"
              r="80"
              cx="100"
              cy="100"
              strokeDasharray={2 * Math.PI * 80}
              strokeDashoffset={2 * Math.PI * 80 * (1 - overallPercent / 100)}
              transform="rotate(-90 100 100)"
            />
          </svg>
          <div className="percent-text">{overallPercent}%</div>
        </div>
        <p className="overall-description">
          Из {cardStatuses.mastered + cardStatuses.learning + cardStatuses.review + cardStatuses.new} карточек освоено: {cardStatuses.mastered}
        </p>
      </div>

      {/* Статусы карточек */}
      <div className="status-cards">
        <div className="status-card new">
          <span className="status-emoji">⚪</span>
          <span className="status-count">{cardStatuses.new}</span>
          <span className="status-label">Новые</span>
        </div>
        <div className="status-card learning">
          <span className="status-emoji">🟡</span>
          <span className="status-count">{cardStatuses.learning}</span>
          <span className="status-label">Изучаются</span>
        </div>
        <div className="status-card mastered">
          <span className="status-emoji">🟢</span>
          <span className="status-count">{cardStatuses.mastered}</span>
          <span className="status-label">Освоены</span>
        </div>
        <div className="status-card review">
          <span className="status-emoji">🔴</span>
          <span className="status-count">{cardStatuses.review}</span>
          <span className="status-label">Повторить</span>
        </div>
      </div>

      {/* Прогресс по таблицам */}
      <div className="tables-grid">
        <h2 className="section-title">📚 Прогресс по таблицам</h2>
        {tableProgresses.map((tp) => (
          <div key={tp.table} className={`table-card ${tp.status}`}>
            <div className="table-header">
              <span className="table-emoji">{getStatusEmoji(tp.status)}</span>
              <h3 className="table-name">Таблица ×{tp.table}</h3>
            </div>
            <div className="table-progress-bar-container">
              <div 
                className="table-progress-bar-fill" 
                style={{ width: `${tp.percent}%`, backgroundColor: getProgressBarColor(tp.percent) }}
              ></div>
            </div>
            <div className="table-stats">
              <span className="table-percent">{tp.percent}%</span>
              <span className="table-fraction">{tp.mastered}/{tp.total}</span>
            </div>
            <span className="table-status-text">{getStatusText(tp.status)}</span>
          </div>
        ))}
      </div>

      {/* Рекомендации */}
      <div className="recommendations-card">
        <h2 className="section-title">💡 Рекомендации</h2>
        <div className="recommendations-list">
          {tableProgresses.filter(tp => tp.percent < 80 && tp.percent > 0).slice(0, 3).map((tp) => (
            <div key={tp.table} className="recommendation-item">
              <span className="rec-emoji">📖</span>
              <span className="rec-text">
                Повторите таблицу <strong>×{tp.table}</strong> — освоено только {tp.percent}%
              </span>
            </div>
          ))}
          {tableProgresses.filter(tp => tp.percent === 100).length > 0 && (
            <div className="recommendation-item success">
              <span className="rec-emoji">🎉</span>
              <span className="rec-text">
                Отлично! Таблиц освоен полностью: {tableProgresses.filter(tp => tp.percent === 100).length}
              </span>
            </div>
          )}
          {tableProgresses.every(tp => tp.percent === 0) && (
            <div className="recommendation-item">
              <span className="rec-emoji">🚀</span>
              <span className="rec-text">
                Начните изучение с таблицы <strong>×1</strong>!
              </span>
            </div>
          )}
        </div>
        <Link to="/learn" className="start-learning-button">
          🎯 Начать обучение
        </Link>
      </div>

      {/* Детализация */}
      <div className="details-card">
        <h2 className="section-title">📋 Детальная информация</h2>
        <div className="details-table">
          <div className="details-header">
            <span>Карточка</span>
            <span>Лёгкость</span>
            <span>Интервал</span>
            <span>Повторы</span>
            <span>Ошибки</span>
            <span>След. повтор</span>
          </div>
          {progress && progress.matrix.slice(0, 10).flatMap((row, i) => 
            row.slice(0, 5).map((cell, j) => (
              <div key={`${i}-${j}`} className="details-row">
                <span>{cell.factor_a} × {cell.factor_b}</span>
                <span>{cell.ease_factor?.toFixed(2) ?? '-'}</span>
                <span>{cell.interval_days ?? '-'} дн.</span>
                <span>{cell.repetitions ?? 0}</span>
                <span>{cell.lapses ?? 0}</span>
                <span>{cell.next_review_at ? new Date(cell.next_review_at).toLocaleDateString('ru-RU') : '-'}</span>
              </div>
            ))
          )}
        </div>
        <p className="details-note">Показаны первые 50 карточек из 100</p>
      </div>
    </div>
  );
};

export default TablePage;
