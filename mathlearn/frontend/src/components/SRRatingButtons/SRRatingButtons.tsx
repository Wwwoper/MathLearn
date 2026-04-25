import React from 'react';
import './SRRatingButtons.css';

export interface SRRatingButtonsProps {
  onRate: (rating: number) => void;
}

const SRRatingButtons: React.FC<SRRatingButtonsProps> = ({ onRate }) => {
  const ratings = [
    { value: 1, label: '😠', color: '#ff4757' },
    { value: 2, label: '😕', color: '#ffa502' },
    { value: 3, label: '😐', color: '#eccc68' },
    { value: 4, label: '🙂', color: '#7bed9f' },
    { value: 5, label: '🤩', color: '#2ed573' },
  ];

  return (
    <div className="sr-rating-buttons">
      {ratings.map((rating) => (
        <button
          key={rating.value}
          className="sr-rating-button"
          onClick={() => onRate(rating.value)}
          style={{ borderColor: rating.color }}
          aria-label={`Оценка ${rating.value} из 5`}
        >
          <span className="sr-rating-emoji">{rating.label}</span>
          <span className="sr-rating-value">{rating.value}</span>
        </button>
      ))}
    </div>
  );
};

export default SRRatingButtons;
