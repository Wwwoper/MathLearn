import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { statsApi, type SpeedDataPoint, type AchievementResponse } from '../api/stats';
import './StatsPage.css';

const StatsPage = () => {
  const [streak, setStreak] = useState({ current_streak: 0, max_streak: 0 });
  const [speedData, setSpeedData] = useState<SpeedDataPoint[]>([]);
  const [achievements, setAchievements] = useState<AchievementResponse[]>([]);
  const [heatmap, setHeatmap] = useState<number[][]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [streakRes, speedRes, achievementsRes, heatmapRes] = await Promise.all([
          statsApi.getStreak(),
          statsApi.getSpeed(30),
          statsApi.getAchievements(),
          statsApi.getHeatmap(),
        ]);

        setStreak(streakRes);
        setSpeedData(speedRes.data_points.map((p) => ({
          date: new Date(p.date).toLocaleDateString('ru-RU'),
          avg_response_ms: p.avg_response_ms,
          accuracy: p.accuracy,
        })));
        setAchievements(achievementsRes.achievements);

        // Преобразование heatmap в матрицу для отображения
        const matrix = heatmapRes.matrix.map((row) =>
          row.map((cell) => cell.error_count)
        );
        setHeatmap(matrix);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div className="stats-loading">Загрузка статистики...</div>;
  }

  return (
    <div className="stats-page">
      <h1 className="stats-title">Статистика</h1>

      {/* Streak Widget */}
      <div className="stats-section">
        <h2 className="section-title">🔥 Серия побед</h2>
        <div className="streak-widget">
          <div className="streak-card">
            <span className="streak-label">Текущая серия</span>
            <span className="streak-value">{streak.current_streak} дней</span>
          </div>
          <div className="streak-card">
            <span className="streak-label">Максимальная серия</span>
            <span className="streak-value">{streak.max_streak} дней</span>
          </div>
        </div>
      </div>

      {/* Heatmap ошибок */}
      <div className="stats-section">
        <h2 className="section-title">📊 Тепловая карта ошибок</h2>
        <div className="heatmap-container">
          <div className="heatmap-grid">
            <div className="heatmap-header"></div>
            {Array.from({ length: 10 }, (_, i) => (
              <div key={`header-b-${i + 1}`} className="heatmap-cell header">
                {i + 1}
              </div>
            ))}
            {heatmap.map((row, aIndex) => (
              <>
                <div key={`header-a-${aIndex + 1}`} className="heatmap-cell header">
                  {aIndex + 1}
                </div>
                {row.map((errorCount, bIndex) => {
                  const intensity = Math.min(errorCount / 5, 1);
                  const bgColor = `rgba(255, ${Math.round(255 * (1 - intensity))}, ${Math.round(255 * (1 - intensity))}, ${0.3 + intensity * 0.7})`;
                  return (
                    <div
                      key={`cell-${aIndex}-${bIndex}`}
                      className="heatmap-cell"
                      style={{ backgroundColor: bgColor }}
                      title={`${aIndex + 1} × ${bIndex + 1}: ${errorCount} ошибок`}
                    >
                      {errorCount > 0 ? errorCount : ''}
                    </div>
                  );
                })}
              </>
            ))}
          </div>
        </div>
      </div>

      {/* Line chart динамики точности */}
      <div className="stats-section">
        <h2 className="section-title">📈 Динамика точности (30 дней)</h2>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={speedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" domain={[0, 100]} />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="accuracy"
                stroke="#8884d8"
                name="Точность (%)"
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avg_response_ms"
                stroke="#82ca9d"
                name="Среднее время (мс)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Сетка достижений */}
      <div className="stats-section">
        <h2 className="section-title">🏆 Достижения</h2>
        <div className="achievements-grid">
          {achievements.map((achievement) => (
            <div
              key={achievement.id}
              className={`achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'}`}
            >
              <div className="achievement-icon">
                {achievement.unlocked ? '🏆' : '🔒'}
              </div>
              <div className="achievement-info">
                <h3 className="achievement-name">{achievement.name}</h3>
                <p className="achievement-description">{achievement.description}</p>
                {achievement.unlocked && achievement.unlocked_at && (
                  <span className="achievement-date">
                    Разблокировано: {new Date(achievement.unlocked_at).toLocaleDateString('ru-RU')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatsPage;
