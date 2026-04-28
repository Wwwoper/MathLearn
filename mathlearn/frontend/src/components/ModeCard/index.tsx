import React from 'react';
import './ModeCard.css';

export interface ModeInfo {
  mode: string;
  title: string;
  description: string;
  icon: string;
  is_pro: boolean;
  primary_metric: string;
}

export interface ModeCardProps {
  mode: ModeInfo;
  selected: boolean;
  onSelect: (mode: string) => void;
  isProUser?: boolean;
}

/**
 * T-LM-15: Компонент карточки сценария обучения
 * 
 * Состояния:
 * - default: обычное отображение
 * - selected: подсвечена рамкой (выбранный режим)
 * - pro-locked: если is_pro && !user.isPro (платный режим для бесплатного пользователя)
 * 
 * Особенности:
 * - Анимация выбора: лёгкий scale-up + смена цвета рамки
 * - Бейдж PRO в правом верхнем углу для платных режимов
 */
const ModeCard: React.FC<ModeCardProps> = ({ 
  mode, 
  selected, 
  onSelect,
  isProUser = false 
}) => {
  const isProLocked = mode.is_pro && !isProUser;
  
  const handleClick = () => {
    if (!isProLocked) {
      onSelect(mode.mode);
    }
  };

  const getCardClassName = () => {
    const classes = ['mode-card'];
    
    if (selected) {
      classes.push('mode-card--selected');
    }
    
    if (isProLocked) {
      classes.push('mode-card--pro-locked');
    }
    
    return classes.join(' ');
  };

  return (
    <div 
      className={getCardClassName()} 
      onClick={handleClick}
      role="button"
      tabIndex={isProLocked ? -1 : 0}
      aria-pressed={selected}
      aria-disabled={isProLocked}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* PRO Badge */}
      {mode.is_pro && (
        <div className="mode-card__pro-badge">
          PRO
        </div>
      )}
      
      {/* Icon */}
      <div className="mode-card__icon">
        {mode.icon}
      </div>
      
      {/* Title */}
      <h3 className="mode-card__title">
        {mode.title}
      </h3>
      
      {/* Description */}
      <p className="mode-card__description">
        {mode.description}
      </p>
      
      {/* Primary Metric */}
      <div className="mode-card__metric">
        <span className="mode-card__metric-label">Метрика:</span>
        <span className="mode-card__metric-value">{mode.primary_metric}</span>
      </div>
      
      {/* Selection Indicator */}
      {selected && (
        <div className="mode-card__selection-indicator">
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" 
              fill="currentColor"
            />
          </svg>
        </div>
      )}
      
      {/* Lock Overlay for Pro */}
      {isProLocked && (
        <div className="mode-card__lock-overlay">
          <svg 
            width="32" 
            height="32" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" 
              fill="currentColor"
            />
          </svg>
          <span>Доступно в PRO</span>
        </div>
      )}
    </div>
  );
};

export default ModeCard;
