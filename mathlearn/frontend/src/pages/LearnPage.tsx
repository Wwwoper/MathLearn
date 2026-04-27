import React, { useState } from 'react';
import { FlashCard } from '../components/FlashCard';
import SRRatingButtons from '../components/SRRatingButtons';
import './LearnPage.css';

interface CardData {
  factorA: number;
  factorB: number;
  answer: number;
  id: number;
}

const LearnPage = () => {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showRating, setShowRating] = useState(false);
  const [isReadyForNext, setIsReadyForNext] = useState(false);

  // Demo data - в реальном приложении будет загружаться из бэкенда
  const cards: CardData[] = [
    { id: 1, factorA: 2, factorB: 3, answer: 6 },
    { id: 2, factorA: 4, factorB: 5, answer: 20 },
    { id: 3, factorA: 6, factorB: 7, answer: 42 },
    { id: 4, factorA: 8, factorB: 9, answer: 72 },
    { id: 5, factorA: 3, factorB: 7, answer: 21 },
  ];

  const handleRate = (rating: number) => {
    console.log(`Rated ${rating}`);
    // Здесь будет логика интервального повторения
    setShowRating(false);
    setIsReadyForNext(true);
  };

  const handleCardFlip = () => {
    if (isReadyForNext) {
      // Переход к следующей карточке
      if (currentCardIndex < cards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1);
        setIsReadyForNext(false);
        setShowRating(false);
      } else {
        alert('Все карточки пройдены!');
        setIsReadyForNext(false);
      }
    } else {
      // Показываем кнопки рейтинга после переворота карточки
      setTimeout(() => {
        setShowRating(true);
      }, 300);
    }
  };

  const currentCard = cards[currentCardIndex];

  return (
    <div className="learn-page">
      <h1>Учим таблицу умножения</h1>
      <div className="progress">
        Карточка {currentCardIndex + 1} из {cards.length}
      </div>
      
      <div onClick={handleCardFlip}>
        <FlashCard
          factorA={currentCard.factorA}
          factorB={currentCard.factorB}
          answer={currentCard.answer}
        />
      </div>

      {showRating && (
        <div className="rating-section">
          <p>Насколько хорошо вы знали ответ?</p>
          <SRRatingButtons onRate={handleRate} />
        </div>
      )}

      {isReadyForNext && (
        <div className="ready-for-next-hint">
          <p>Нажмите на карточку, чтобы продолжить</p>
        </div>
      )}
    </div>
  );
};

export default LearnPage;
