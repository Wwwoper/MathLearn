import React, { useState } from 'react';
import './LearningModeSelector.css';

export type LearningMode = 
  | 'classic' 
  | 'sprinter' 
  | 'weak_spots' 
  | 'streak_hunter' 
  | 'fighter' 
  | 'zen';

interface ModeCard {
  id: LearningMode;
  title: string;
  emoji: string;
  description: string;
  tagline: string;
  color: string;
}

const modes: ModeCard[] = [
  {
    id: 'classic',
    title: 'Классик',
    emoji: '🗺️',
    tagline: 'Шаг за шагом, без спешки',
    description: 'Строгий порядок: от ×2 до ×10. Новая таблица открывается только после освоения предыдущей.',
    color: '#4facfe'
  },
  {
    id: 'sprinter',
    title: 'Спринтер',
    emoji: '⚡',
    tagline: 'Мне важна скорость!',
    description: 'Режим Drill с таймером 5 сек. Главная цель — отвечать быстрее молнии.',
    color: '#f093fb'
  },
  {
    id: 'weak_spots',
    title: 'Анализ слабых мест',
    emoji: '🧠',
    tagline: 'Исправим ошибки',
    description: 'Ежедневная работа только над теми примерами, где ты ошибаешься чаще всего.',
    color: '#fa709a'
  },
  {
    id: 'streak_hunter',
    title: 'Стрик-Охотник',
    emoji: '🔥',
    tagline: 'Каждый день по чуть-чуть',
    description: 'Короткие сессии по 3 минуты. Главное — не прерывать серию побед!',
    color: '#ff9a9e'
  },
  {
    id: 'fighter',
    title: 'Боец',
    emoji: '🎮',
    tagline: 'Хочу соревноваться',
    description: 'Ежедневные вызовы и рейтинг. Обгоняй свои вчерашние результаты и друзей.',
    color: '#a18cd1'
  },
  {
    id: 'zen',
    title: 'Дзен',
    emoji: '🌙',
    tagline: 'Без давления и таймеров',
    description: 'Спокойный режим без ограничений по времени. Учись в своем ритме с подсказками.',
    color: '#84fab0'
  }
];

interface LearningModeSelectorProps {
  onSelect: (mode: LearningMode) => void;
  currentMode?: LearningMode;
}

const LearningModeSelector: React.FC<LearningModeSelectorProps> = ({ onSelect, currentMode }) => {
  const [selected, setSelected] = useState<LearningMode | null>(currentMode || null);

  const handleConfirm = () => {
    if (selected) {
      onSelect(selected);
    }
  };

  return (
    <div className="mode-selector-container">
      <div className="mode-header">
        <h2>Как ты хочешь учиться? 🤔</h2>
        <p>Выбери свой путь к знаниям!</p>
      </div>

      <div className="modes-grid">
        {modes.map((mode) => (
          <div
            key={mode.id}
            className={`mode-card ${selected === mode.id ? 'selected' : ''}`}
            onClick={() => setSelected(mode.id)}
            style={{ 
              borderColor: selected === mode.id ? mode.color : 'transparent',
              boxShadow: selected === mode.id ? `0 0 20px ${mode.color}66` : 'none'
            }}
          >
            <div className="mode-emoji" style={{ fontSize: '3rem' }}>{mode.emoji}</div>
            <h3>{mode.title}</h3>
            <div className="mode-tagline">{mode.tagline}</div>
            <p className="mode-desc">{mode.description}</p>
            
            {selected === mode.id && (
              <div className="check-mark">✅ Выбрано</div>
            )}
          </div>
        ))}
      </div>

      <div className="mode-actions">
        <button 
          className="confirm-btn" 
          onClick={handleConfirm}
          disabled={!selected}
        >
          {currentMode ? 'Сохранить режим' : 'Начать обучение!'} 🚀
        </button>
      </div>
    </div>
  );
};

export default LearningModeSelector;
