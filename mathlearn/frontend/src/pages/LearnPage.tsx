import React, { useState, useEffect } from 'react';
import { FlashCard } from '../components/FlashCard';
import SRRatingButtons from '../components/SRRatingButtons';
import './LearnPage.css';

interface CardData {
  factorA: number;
  factorB: number;
  answer: number;
  id: number;
}

interface StatsData {
  excellent: number;
  good: number;
  hard: number;
  repeat: number;
}

const LearnPage = () => {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showRating, setShowRating] = useState(false);
  const [isReadyForNext, setIsReadyForNext] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [stats, setStats] = useState<StatsData>({ excellent: 0, good: 0, hard: 0, repeat: 0 });

  // Demo data - в реальном приложении будет загружаться из бэкенда
  const cards: CardData[] = [
    { id: 1, factorA: 2, factorB: 3, answer: 6 },
    { id: 2, factorA: 4, factorB: 5, answer: 20 },
    { id: 3, factorA: 6, factorB: 7, answer: 42 },
    { id: 4, factorA: 8, factorB: 9, answer: 72 },
    { id: 5, factorA: 3, factorB: 7, answer: 21 },
  ];

  // Загрузка статистики из localStorage при монтировании
  useEffect(() => {
    const savedStats = localStorage.getItem('flashcard-stats');
    if (savedStats) {
      setStats(JSON.parse(savedStats));
    }
  }, []);

  // Сохранение статистики в localStorage
  const saveStats = (newStats: StatsData) => {
    localStorage.setItem('flashcard-stats', JSON.stringify(newStats));
    setStats(newStats);
  };

  const handleRate = (rating: number) => {
    console.log(`Rated ${rating}`);
    
    // Обновление статистики на основе рейтинга
    const newStats = { ...stats };
    
    if (rating === 5) {
      newStats.excellent += 1;
    } else if (rating === 4) {
      newStats.good += 1;
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
  };

  const handleHome = () => {
    // Навигация на главную страницу
    window.location.href = '/';
  };

  // Вычисление процентов для круговой диаграммы
  const totalCards = stats.excellent + stats.good + stats.hard + stats.repeat;
  const excellentPercent = totalCards > 0 ? (stats.excellent / totalCards) * 100 : 0;
  const goodPercent = totalCards > 0 ? ((stats.excellent + stats.good) / totalCards) * 100 : 0;
  const hardPercent = totalCards > 0 ? ((stats.excellent + stats.good + stats.hard) / totalCards) * 100 : 0;

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

  const currentCard = cards[currentCardIndex];

  return (
    <div className="learn-page">
      <h1>Учим таблицу умножения</h1>
      <div className="progress">
        Карточка {currentCardIndex + 1} из {cards.length}
      </div>
      
      <FlashCard
        factorA={currentCard.factorA}
        factorB={currentCard.factorB}
        answer={currentCard.answer}
        isFlipped={isFlipped}
        onFlip={handleCardFlip}
      />

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
    </div>
  );
};

export default LearnPage;
