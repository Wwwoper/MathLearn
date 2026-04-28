import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import type { LearningMode } from '../components/LearningModeSelector/LearningModeSelector';

export interface SRCard {
  id: number;
  factor_a: number;
  factor_b: number;
  answer: number;
  ease_factor: number;
  next_review_at?: string;
  hints_remaining?: number;
  is_locked?: boolean;
}

export interface QueueResponse {
  cards: SRCard[];
  progress?: {
    current_table: number;
    next_table: number;
    avg_ease_factor: number;
    unlock_progress: number; // 0-100
  };
}

interface UseSRQueueOptions {
  mode: LearningMode;
  tableId?: number;
  limit?: number;
}

interface UseSRQueueReturn {
  cards: SRCard[];
  isLoading: boolean;
  error: Error | null;
  progress: QueueResponse['progress'] | null;
  refreshQueue: () => Promise<void>;
}

/**
 * T-LM-17: Хук для получения очереди карточек Spaced Repetition
 * - Передает mode в запрос GET /api/sr/queue?mode=...
 * - В режиме zen: возвращает карточки с hints_remaining > 0
 * - В режиме classic: возвращает прогресс разблокировки следующей таблицы
 */
export const useSRQueue = ({ mode, tableId, limit = 20 }: UseSRQueueOptions): UseSRQueueReturn => {
  const [cards, setCards] = useState<SRCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [progress, setProgress] = useState<QueueResponse['progress'] | null>(null);

  const fetchQueue = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        mode,
        limit: limit.toString(),
      });
      
      if (tableId) {
        params.append('table_id', tableId.toString());
      }
      
      const response = await apiClient.get<QueueResponse>(`/api/sr/queue?${params.toString()}`);
      setCards(response.data.cards);
      setProgress(response.data.progress || null);
    } catch (err) {
      console.error('Failed to fetch SR queue:', err);
      setError(err instanceof Error ? err : new Error('Unknown error'));
      setCards([]);
      setProgress(null);
    } finally {
      setIsLoading(false);
    }
  }, [mode, tableId, limit]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  return {
    cards,
    isLoading,
    error,
    progress,
    refreshQueue: fetchQueue,
  };
};
