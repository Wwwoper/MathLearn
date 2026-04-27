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
  return (
    <div className="flashcard-container">
      <div
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={onFlip}
      >
        <div className="flashcard-face flashcard-front">
          <div className="question">
            <span className="factor">{factorA}</span>
            <span className="operator">×</span>
            <span className="factor">{factorB}</span>
            <span className="operator">=</span>
            <span className="result-placeholder">?</span>
          </div>
          <p className="hint">Нажмите, чтобы увидеть ответ</p>
        </div>
        <div className="flashcard-face flashcard-back">
          <div className="answer">{answer}</div>
        </div>
      </div>
    </div>
  );
};
