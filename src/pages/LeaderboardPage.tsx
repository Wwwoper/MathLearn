import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import './LeaderboardPage.css';

interface LeaderboardEntry {
  id: string;
  username: string;
  avatarUrl: string;
  points: number;
  badges: string[];
  rank: number;
}

const mockLeaderboardData: LeaderboardEntry[] = [
  { id: '1', username: 'SpeedMath', avatarUrl: 'https://i.pravatar.cc/150?u=1', points: 15420, badges: ['🔥', '⚡'], rank: 1 },
  { id: '2', username: 'NumNinja', avatarUrl: 'https://i.pravatar.cc/150?u=2', points: 14850, badges: ['🛡️'], rank: 2 },
  { id: '3', username: 'CalcKing', avatarUrl: 'https://i.pravatar.cc/150?u=3', points: 13200, badges: ['🏆'], rank: 3 },
  { id: '4', username: 'QuickDraw', avatarUrl: 'https://i.pravatar.cc/150?u=4', points: 12100, badges: [], rank: 4 },
  { id: '5', username: 'MathWiz', avatarUrl: 'https://i.pravatar.cc/150?u=5', points: 11500, badges: ['✨'], rank: 5 },
  { id: '6', username: 'DigitDuel', avatarUrl: 'https://i.pravatar.cc/150?u=6', points: 10900, badges: [], rank: 6 },
  { id: '7', username: 'SumSurfer', avatarUrl: 'https://i.pravatar.cc/150?u=7', points: 9800, badges: ['🌊'], rank: 7 },
  { id: '8', username: 'Prodigy', avatarUrl: 'https://i.pravatar.cc/150?u=8', points: 9200, badges: [], rank: 8 },
  { id: '9', username: 'FactorFox', avatarUrl: 'https://i.pravatar.cc/150?u=9', points: 8500, badges: ['🦊'], rank: 9 },
  { id: '10', username: 'TableTitan', avatarUrl: 'https://i.pravatar.cc/150?u=10', points: 7900, badges: [], rank: 10 },
];

const LeaderboardPage: React.FC = () => {
  const { user, updateUserLearningMode } = useAuthStore();
  const [period, setPeriod] = useState<'current' | 'previous'>('current');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      // Имитация API запроса: GET /api/leaderboard?period=...
      await new Promise(resolve => setTimeout(resolve, 500));
      
      let data = [...mockLeaderboardData];
      if (user) {
        const currentUserExists = data.some(entry => entry.id === user.id);
        if (!currentUserExists) {
          data.push({
            id: user.id,
            username: user.username || 'User',
            avatarUrl: user.avatarUrl || 'https://i.pravatar.cc/150?u=default',
            points: Math.floor(Math.random() * 5000) + 5000,
            badges: [],
            rank: 11
          });
        }
      }
      setLeaderboard(data);
      setIsLoading(false);
    };

    fetchData();
  }, [period, user]);

  const handleSwitchMode = () => {
    if (user) {
      updateUserLearningMode('fighter');
    }
  };

  if (user?.learning_mode !== 'fighter') {
    return (
      <div className="leaderboard-access-denied">
        <div className="access-denied-content">
          <h1>🥊 Доступно только для Бойцов</h1>
          <p>
            Таблица лидеров — это арена для режима <strong>Fighter</strong>.
            Сражайтесь с другими игроками, зарабатывайте очки и поднимайтесь в рейтинге!
          </p>
          <div className="mode-preview">
            <div className="feature-badge">🏆 Топ-10 игроков</div>
            <div className="feature-badge">📅 Еженедельные сезоны</div>
            <div className="feature-badge">🎖️ Уникальные бейджи</div>
          </div>
          <button className="switch-mode-btn" onClick={handleSwitchMode}>
            Стать Бойцом и войти в рейтинг
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="leaderboard-page">
      <header className="leaderboard-header">
        <h1>🏆 Таблица Лидеров</h1>
        <div className="period-switcher">
          <button
            className={`period-btn ${period === 'current' ? 'active' : ''}`}
            onClick={() => setPeriod('current')}
          >
            Эта неделя
          </button>
          <button
            className={`period-btn ${period === 'previous' ? 'active' : ''}`}
            onClick={() => setPeriod('previous')}
          >
            Прошлая неделя
          </button>
        </div>
      </header>

      <div className="leaderboard-content">
        {isLoading ? (
          <div className="loading-state">Загрузка рейтинга...</div>
        ) : (
          <div className="leaderboard-table-wrapper">
            <table className="leaderboard-table">
              <thead>
                <tr>
                  <th className="col-rank">#</th>
                  <th className="col-player">Игрок</th>
                  <th className="col-badges">Бейджи</th>
                  <th className="col-points">Очки</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry) => {
                  const isCurrentUser = user && entry.id === user.id;
                  return (
                    <tr 
                      key={entry.id} 
                      className={`leaderboard-row ${isCurrentUser ? 'current-user-row' : ''} ${entry.rank <= 3 ? `top-${entry.rank}` : ''}`}
                    >
                      <td className="col-rank">
                        {entry.rank <= 3 ? (
                          <span className="rank-medal">{entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉'}</span>
                        ) : (
                          <span className="rank-number">{entry.rank}</span>
                        )}
                      </td>
                      <td className="col-player">
                        <div className="player-info">
                          <img src={entry.avatarUrl} alt={entry.username} className="player-avatar" />
                          <span className="player-name">{entry.username}</span>
                        </div>
                      </td>
                      <td className="col-badges">
                        <div className="badges-list">
                          {entry.badges.length > 0 ? (
                            entry.badges.map((badge, idx) => (
                              <span key={idx} className="badge-item" title={`Badge ${idx + 1}`}>{badge}</span>
                            ))
                          ) : (
                            <span className="no-badges">-</span>
                          )}
                        </div>
                      </td>
                      <td className="col-points">
                        <span className="points-value">{entry.points.toLocaleString()}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        
        <div className="leaderboard-footer">
          <p>Сезон обновляется каждый понедельник в 00:00 UTC.</p>
        </div>
      </div>
    </div>
  );
};

export default LeaderboardPage;
