import React, { useState, useEffect, useCallback } from 'react';
import './TimerDrill.css';

interface Question {
  factorA: number;
  factorB: number;
  answer: number;
}

interface TimerDrillProps {
  duration?: number; // продолжительность в секундах (по умолчанию 60)
  onScoreUpdate?: (score: number, total: number) => void;
  onFinish?: (score: number, total: number, timeSpent: number) => void;
}

const generateQuestion = (): Question => {
  const factorA = Math.floor(Math.random() * 9) + 2; // 2-10
  const factorB = Math.floor(Math.random() * 9) + 2; // 2-10
  return {
    factorA,
    factorB,
    answer: factorA * factorB,
  };
};

const TimerDrill: React.FC<TimerDrillProps> = ({
  duration = 60,
  onScoreUpdate,
  onFinish,
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(duration);
  const [currentQuestion, setCurrentQuestion] = useState<Question>(generateQuestion());
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [score, setScore] = useState<number>(0);
  const [totalAttempts, setTotalAttempts] = useState<number>(0);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | null>(null);

  // Таймер обратного отсчета
  useEffect(() => {
    if (timeLeft <= 0 || isFinished) {
      setIsFinished(true);
      if (onFinish) {
        onFinish(score, totalAttempts, duration - timeLeft);
      }
      return;
    }

    const timerId = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timerId);
  }, [timeLeft, isFinished, onFinish, score, totalAttempts, duration]);

  // Обработка отправки ответа
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!userAnswer.trim()) return;

      const numericAnswer = parseInt(userAnswer, 10);
      const isCorrect = numericAnswer === currentQuestion.answer;

      setTotalAttempts((prev) => prev + 1);

      if (isCorrect) {
        setScore((prev) => prev + 1);
        setFeedback('correct');
        if (onScoreUpdate) {
          onScoreUpdate(score + 1, totalAttempts + 1);
        }
      } else {
        setFeedback('wrong');
        if (onScoreUpdate) {
          onScoreUpdate(score, totalAttempts + 1);
        }
      }

      // Небольшая задержка перед следующим вопросом для отображения фидбека
      setTimeout(() => {
        setCurrentQuestion(generateQuestion());
        setUserAnswer('');
        setFeedback(null);
      }, 300);
    },
    [userAnswer, currentQuestion, score, totalAttempts, onScoreUpdate]
  );

  // Форматирование времени (мм:сс)
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Перезапуск тренировки
  const handleRestart = () => {
    setTimeLeft(duration);
    setCurrentQuestion(generateQuestion());
    setUserAnswer('');
    setScore(0);
    setTotalAttempts(0);
    setIsFinished(false);
    setFeedback(null);
  };

  if (isFinished) {
    const accuracy = totalAttempts > 0 ? Math.round((score / totalAttempts) * 100) : 0;

    return (
      <div className="timer-drill timer-drill--finished">
        <div className="timer-drill__results">
          <h2 className="timer-drill__title">Время вышло!</h2>
          <div className="timer-drill__stats">
            <div className="timer-drill__stat">
              <span className="timer-drill__stat-value">{score}</span>
              <span className="timer-drill__stat-label">Правильных ответов</span>
            </div>
            <div className="timer-drill__stat">
              <span className="timer-drill__stat-value">{totalAttempts}</span>
              <span className="timer-drill__stat-label">Всего попыток</span>
            </div>
            <div className="timer-drill__stat">
              <span className="timer-drill__stat-value">{accuracy}%</span>
              <span className="timer-drill__stat-label">Точность</span>
            </div>
          </div>
          <button className="timer-drill__restart-btn" onClick={handleRestart}>
            Начать заново
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="timer-drill">
      <div className="timer-drill__header">
        <div className="timer-drill__timer">
          <span className={`timer-drill__time ${timeLeft <= 10 ? 'timer-drill__time--urgent' : ''}`}>
            {formatTime(timeLeft)}
          </span>
        </div>
        <div className="timer-drill__score">
          <span className="timer-drill__score-value">{score}</span>
          <span className="timer-drill__score-label">/ {totalAttempts}</span>
        </div>
      </div>

      <form className="timer-drill__question-area" onSubmit={handleSubmit}>
        <div className="timer-drill__question">
          <span className="timer-drill__factor">{currentQuestion.factorA}</span>
          <span className="timer-drill__operator">×</span>
          <span className="timer-drill__factor">{currentQuestion.factorB}</span>
          <span className="timer-drill__operator">=</span>
          <span className="timer-drill__question-mark">?</span>
        </div>

        <div className="timer-drill__input-group">
          <input
            type="number"
            className="timer-drill__input"
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="Ваш ответ"
            autoFocus
            disabled={!!feedback}
          />
          <button
            type="submit"
            className="timer-drill__submit-btn"
            disabled={!userAnswer.trim() || !!feedback}
          >
            Ответить
          </button>
        </div>

        {feedback && (
          <div className={`timer-drill__feedback timer-drill__feedback--${feedback}`}>
            {feedback === 'correct' ? '✓ Правильно!' : `✗ Ошибка! Правильный ответ: ${currentQuestion.answer}`}
          </div>
        )}
      </form>

      <div className="timer-drill__progress">
        <div
          className="timer-drill__progress-bar"
          style={{ width: `${((duration - timeLeft) / duration) * 100}%` }}
        />
      </div>
    </div>
  );
};

export default TimerDrill;
