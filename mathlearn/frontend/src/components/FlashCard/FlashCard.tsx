import React, { useState } from 'react';
import './FlashCard.css';

interface FlashCardProps {
  factorA: number;
  factorB: number;
  answer: number;
  isFlipped: boolean;
  onFlip: () => void;
  mode?: 'classic' | 'zen';
}

export const FlashCard: React.FC<FlashCardProps> = ({ 
  factorA, 
  factorB, 
  answer, 
  isFlipped, 
  onFlip,
  mode = 'classic'
}) => {
  const [userAnswer, setUserAnswer] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);

  const handleShowAnswer = () => {
    if (!isFlipped) {
      onFlip();
    }
  };

  const handleZenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(userAnswer, 10);
    setIsCorrect(parsed === answer);
    setShowResult(true);
  };

  const handleZenReset = () => {
    setUserAnswer('');
    setShowResult(false);
    setIsCorrect(null);
    onFlip();
  };

  // Режим zen: только вопрос и input, без переворота
  if (mode === 'zen') {
    return (
      <div className="flashcard-container zen-mode">
        <div className="flashcard-face flashcard-front">
          <div className="question">
            <span className="factor">{factorA}</span>
            <span className="operator">×</span>
            <span className="factor">{factorB}</span>
            <span className="operator">=</span>
            {!showResult ? (
              <form className="zen-input-form" onSubmit={handleZenSubmit}>
                <input
                  type="number"
                  className="zen-answer-input"
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="?"
                  autoFocus
                />
                <button type="submit" className="zen-submit-btn">
                  ✓
                </button>
              </form>
            ) : (
              <span className={`zen-result ${isCorrect ? 'correct' : 'incorrect'}`}>
                {isCorrect ? '✅' : '❌'} {answer}
              </span>
            )}
          </div>
          {showResult && (
            <button className="zen-next-btn" onClick={handleZenReset}>
              Далее ➡️
            </button>
          )}
        </div>
      </div>
    );
  }

  // Классический режим с переворотом
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
