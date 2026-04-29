import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FlashCard } from '../components/FlashCard';
import SRRatingButtons from '../components/SRRatingButtons';
import Confetti from 'react-confetti';
import { useAuthStore } from '../store/useAuthStore';
import { useSRQueue } from '../hooks/useSRQueue';
import apiClient from '../api/client';
import './LearnPage.css';

interface StatsData {
  excellent: number;
  good: number;
  hard: number;
  repeat: number;
}

const LearnPage = () => {
  const navigate = useNavigate();
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showRating, setShowRating] = useState(false);
  const [isReadyForNext, setIsReadyForNext] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [stats, setStats] = useState<StatsData>({ excellent: 0, good: 0, hard: 0, repeat: 0 });
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });
  const [sessionStarted, setSessionStarted] = useState(false);
  const [dailyChallengeAccepted, setDailyChallengeAccepted] = useState(false);
  
  // Получаем текущий режим обучения из store
  const { user } = useAuthStore();
  const currentMode = user?.learning_mode || 'classic';
  
  // T-LM-18: Для streak_hunter ограничиваем сессию до 5 вопросов
  const sessionLimit = currentMode === 'streak_hunter' ? 5 : 20;
  
  // Используем хук useSRQueue для получения очереди карточек (T-LM-17)
  const { cards: srCards, isLoading, progress } = useSRQueue({
    mode: currentMode,
    limit: sessionLimit,
  });
  
  // Преобразуем SRCard в формат для совместимости с существующим кодом
  const cards = srCards.map(card => ({
    id: card.id,
    factorA: card.factor_a,
    factorB: card.factor_b,
    answer: card.answer,
    hints_remaining: card.hints_remaining,
  }));

  // Загрузка статистики из localStorage при монтировании
  useEffect(() => {
    const savedStats = localStorage.getItem('flashcard-stats');
    if (savedStats) {
      setStats(JSON.parse(savedStats));
    }
    
    // Установка размера окна для конфетти
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight
    });

    // T-LM-18: Автоматический запуск сессии для streak_hunter
    if (currentMode === 'streak_hunter' && !sessionStarted && srCards.length > 0) {
      setSessionStarted(true);
      setIsFlipped(false);
      setShowRating(false);
    }
  }, [currentMode, sessionStarted, srCards.length]);

  // Сохранение статистики в localStorage
  const saveStats = (newStats: StatsData) => {
    localStorage.setItem('flashcard-stats', JSON.stringify(newStats));
    setStats(newStats);
  };

  const handleRate = async (rating: number) => {
    console.log(`Rated ${rating}`);
    
    // Отправляем рейтинг на сервер для обновления SM-2
    const currentCard = cards[currentCardIndex];
    try {
      await apiClient.post('/sr/review', {
        card_id: currentCard.id,
        rating: rating,
        response_time_ms: 0, // Можно добавить замер времени ответа
      });
      console.log('Review submitted successfully');
    } catch (error) {
      console.error('Failed to submit review:', error);
    }
    
    // Обновление статистики на основе рейтинга
    const newStats = { ...stats };
    
    if (rating === 5) {
      newStats.excellent += 1;
      // Запуск конфетти для оценки "Отлично"
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 3000);
    } else if (rating === 4) {
      newStats.good += 1;
      // Запуск конфетти для оценки "Хорошо"
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 2000);
    } else if (rating === 3) {
      newStats.hard += 1;
    } else {
      newStats.repeat += 1;
    }
    
    saveStats(newStats);
    
    setShowRating(false);
    setIsReadyForNext(true);
  };

  const handleNextCard = () => {
    // Переход к следующей карточке
    if (currentCardIndex < cards.length - 1) {
      setIsFlipped(false);
      setTimeout(() => {
        setCurrentCardIndex(prev => prev + 1);
        setIsReadyForNext(false);
        setShowRating(false);
      }, 300);
    } else {
      // Показываем экран статистики после прохождения всех карточек
      setShowStats(true);
      setIsReadyForNext(false);
      setIsFlipped(false);
    }
  };

  const handleCardFlip = () => {
    if (!isFlipped) {
      // Показываем кнопки рейтинга после переворота карточки
      setIsFlipped(true);
      setTimeout(() => {
        setShowRating(true);
      }, 300);
    }
  };

  const handleRetry = () => {
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setShowRating(false);
    setIsReadyForNext(false);
    setShowStats(false);
    setSessionStarted(false);
    setDailyChallengeAccepted(false);
  };

  const handleHome = () => {
    // Навигация на главную страницу с использованием navigate
    navigate('/');
  };

  // T-LM-18: Обработчик для принятия ежедневного вызова в режиме fighter
  const handleAcceptDailyChallenge = () => {
    setDailyChallengeAccepted(true);
    setIsFlipped(false);
    setShowRating(false);
    console.log('Daily challenge accepted!');
  };

  // Вычисление процентов для круговой диаграммы
  const totalCards = stats.excellent + stats.good + stats.hard + stats.repeat;
  const excellentPercent = totalCards > 0 ? (stats.excellent / totalCards) * 100 : 0;
  const goodPercent = totalCards > 0 ? ((stats.excellent + stats.good) / totalCards) * 100 : 0;
  const hardPercent = totalCards > 0 ? ((stats.excellent + stats.good + stats.hard) / totalCards) * 100 : 0;

  // Экран загрузки
  if (isLoading) {
    return (
      <div className="learn-page">
        <div className="loading-screen">
          <h2>Загрузка карточек...</h2>
        </div>
      </div>
    );
  }

  // Экран статистики
  if (showStats) {
    return (
      <div className="learn-page">
        <div className="stats-screen">
          <h2>🎉 Статистика</h2>
          
          <div className="pie-chart-container" style={{
            '--excellent-percent': `${excellentPercent}%`,
            '--good-percent': `${goodPercent}%`,
            '--hard-percent': `${hardPercent}%`,
          } as React.CSSProperties}>
            <div className="pie-chart"></div>
            <div className="pie-chart-center">
              <span>{totalCards}</span>
              <span className="pie-chart-label">карточек</span>
            </div>
          </div>

          <div className="stats-categories">
            <div className="stat-category easy">
              <span className="emoji">😊</span>
              <span className="label">Легко</span>
              <span className="count">{stats.excellent}</span>
            </div>
            <div className="stat-category good">
              <span className="emoji">👍</span>
              <span className="label">Хорошо</span>
              <span className="count">{stats.good}</span>
            </div>
            <div className="stat-category hard">
              <span className="emoji">🤔</span>
              <span className="label">Трудно</span>
              <span className="count">{stats.hard}</span>
            </div>
            <div className="stat-category repeat">
              <span className="emoji">📚</span>
              <span className="label">Повторить</span>
              <span className="count">{stats.repeat}</span>
            </div>
          </div>

          <div className="stats-buttons">
            <button className="stats-btn retry" onClick={handleRetry}>
              🔄 Пройти ещё раз
            </button>
            <button className="stats-btn home" onClick={handleHome}>
              🏠 На главную
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Если карточки не загружены
  if (cards.length === 0) {
    return (
      <div className="learn-page">
        <div className="empty-queue">
          <h2>📭 Нет карточек для изучения</h2>
          <p>Вы прошли все доступные карточки в этом режиме!</p>
          <button className="stats-btn home" onClick={handleHome}>
            🏠 На главную
          </button>
        </div>
      </div>
    );
  }

  const currentCard = cards[currentCardIndex];

  return (
    <div className="learn-page">
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={200}
          colors={['#ff416c', '#ff4b2b', '#4CAF50', '#2196F3', '#FFC107']}
        />
      )}
      
      <h1>Учим таблицу умножения</h1>
      
      {/* T-LM-17: Прогресс-бар разблокировки для режима classic */}
      {currentMode === 'classic' && progress && (
        <div className="unlock-progress">
          <div className="progress-info">
            <span>Таблица ×{progress.current_table}</span>
            <span>→ ×{progress.next_table}</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress.unlock_progress}%` }}
            />
          </div>
          <div className="progress-details">
            Средний EF: {progress.avg_ease_factor.toFixed(2)} / 2.0
          </div>
        </div>
      )}

      {/* T-LM-18: Кнопка принятия вызова для режима fighter */}
      {currentMode === 'fighter' && !dailyChallengeAccepted && (
        <div className="daily-challenge-section">
          <h2>🏆 Ежедневный вызов</h2>
          <p>Готов принять вызов дня?</p>
          <button className="accept-challenge-btn" onClick={handleAcceptDailyChallenge}>
            ⚔️ Принять вызов дня
          </button>
        </div>
      )}
      
      {/* Показываем прогресс и карточку только если не в режиме ожидания fighter */}
      {(currentMode !== 'fighter' || dailyChallengeAccepted) && (
        <>
          <div className="progress">
            Карточка {currentCardIndex + 1} из {cards.length}
          </div>
          
          <FlashCard
            factorA={currentCard.factorA}
            factorB={currentCard.factorB}
            answer={currentCard.answer}
            isFlipped={isFlipped}
            onFlip={handleCardFlip}
            mode={currentMode === 'zen' ? 'zen' : 'classic'}
          />

          {/* T-LM-17: Подсказка для режима zen */}
          {currentMode === 'zen' && currentCard.hints_remaining !== undefined && currentCard.hints_remaining > 0 && (
            <div className="zen-hint">
              💡 Подсказок осталось: {currentCard.hints_remaining}
            </div>
          )}

          {showRating && (
            <div className="rating-section">
              <p>Насколько хорошо вы знали ответ?</p>
              <SRRatingButtons onRate={handleRate} />
            </div>
          )}

          {isReadyForNext && (
            <div className="ready-for-next-section">
              <button className="next-card-button" onClick={handleNextCard}>
                Далее ➡️
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default LearnPage;
