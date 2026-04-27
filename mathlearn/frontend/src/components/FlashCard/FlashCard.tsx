import React from 'react';
import './FlashCard.css';

interface FlashCardProps {
  factorA: number;
  factorB: number;
  answer: number;
  isFlipped: boolean;
  onFlip: () => void;
}

export const FlashCard: React.FC<FlashCardProps> = ({ factorA, factorB, answer, isFlipped, onFlip }) => {
  const handleShowAnswer = () => {
    if (!isFlipped) {
      onFlip();
    }
  };

  return (
    <div className="flashcard-container">
      <div
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
      >
        <div className="flashcard-face flashcard-front">
          <div className="question">
            <span className="factor">{factorA}</span>
            <span className="operator">×</span>
            <span className="factor">{factorB}</span>
            <span className="operator">=</span>
            <span className="result-placeholder">?</span>
          </div>
          {!isFlipped && (
            <button className="show-answer-button" onClick={handleShowAnswer}>
              👆 Показать ответ
            </button>
          )}
        </div>
        <div className="flashcard-face flashcard-back">
          <div className="answer">{answer}</div>
        </div>
      </div>
    </div>
  );
};
