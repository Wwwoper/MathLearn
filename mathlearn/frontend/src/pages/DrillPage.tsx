import React from 'react';
import TimerDrill from '../components/TimerDrill';
import './DrillPage.css';

const DrillPage: React.FC = () => {
  const handleScoreUpdate = (score: number, total: number) => {
    console.log(`Current score: ${score}/${total}`);
  };

  const handleFinish = (score: number, total: number, timeSpent: number) => {
    console.log(`Drill finished! Score: ${score}/${total}, Time spent: ${timeSpent}s`);
    // Здесь можно отправить результаты на сервер или сохранить в статистику
  };

  return (
    <div className="drill-page">
      <header className="drill-page__header">
        <h1 className="drill-page__title">Математический дрилл</h1>
        <p className="drill-page__subtitle">
          Решайте примеры на время! У вас есть 60 секунд.
        </p>
      </header>
      
      <main className="drill-page__main">
        <TimerDrill
          duration={60}
          onScoreUpdate={handleScoreUpdate}
          onFinish={handleFinish}
        />
      </main>
    </div>
  );
};

export default DrillPage;
