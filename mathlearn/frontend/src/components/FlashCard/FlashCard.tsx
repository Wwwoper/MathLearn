import React, { useState } from 'react';
import './FlashCard.css';

interface FlashCardProps {
  factorA: number;
  factorB: number;
  answer: number;
  isFlipped: boolean;
  onFlip: () => void;
}

export const FlashCard: React.FC<FlashCardProps> = ({ factorA, factorB, answer, isFlipped, onFlip }) => {
  const [clickCount, setClickCount] = useState(0);
  const [showDoubleTapHint, setShowDoubleTapHint] = useState(false);

  const handleCardClick = () => {
    if (isFlipped) {
      // Если уже перевернута, просто игнорируем клик
      return;
    }

    const newCount = clickCount + 1;
    setClickCount(newCount);

    if (newCount === 1) {
      // Первый клик - показываем подсказку
      setShowDoubleTapHint(true);
      setTimeout(() => {
        setClickCount(0);
        setShowDoubleTapHint(false);
      }, 1500);
    } else if (newCount === 2) {
      // Двойной клик - переворачиваем
      setClickCount(0);
      setShowDoubleTapHint(false);
      onFlip();
    }
  };

  return (
    <div className="flashcard-container">
      <div
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={handleCardClick}
      >
        <div className="flashcard-face flashcard-front">
          <div className="question">
            <span className="factor">{factorA}</span>
            <span className="operator">×</span>
            <span className="factor">{factorB}</span>
            <span className="operator">=</span>
            <span className="result-placeholder">?</span>
          </div>
          {!showDoubleTapHint && (
            <p className="hint">Нажмите 2 раза, чтобы увидеть ответ 👆👆</p>
          )}
          {showDoubleTapHint && (
            <p className="hint double-tap-hint">Ещё раз! 👆</p>
          )}
        </div>
        <div className="flashcard-face flashcard-back">
          <div className="answer">{answer}</div>
        </div>
      </div>
    </div>
  );
};
