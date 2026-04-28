import apiClient from './client';
import type { LearningMode } from '../components/LearningModeSelector';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  learning_mode: LearningMode;
  xp_multiplier: number;
  streak_freeze_count: number;
  current_streak: number;
  best_streak: number;
}

export interface ModeConfig {
  mode: LearningMode;
  title: string;
  description: string;
  has_timer: boolean;
  time_limit_sec?: number;
  unlimited_hints: boolean;
  preserves_streak: boolean;
}

export interface ProfileResponse {
  profile: UserProfile;
  mode_config: ModeConfig;
}

export const profileApi = {
  getProfile: async (): Promise<ProfileResponse> => {
    const response = await apiClient.get('/api/profile/');
    return response.data;
  },

  updateMode: async (mode: LearningMode): Promise<ProfileResponse> => {
    const response = await apiClient.post('/api/profile/mode', { learning_mode: mode });
    return response.data;
  },

  getMode: async (): Promise<ModeConfig> => {
    const response = await apiClient.get('/api/profile/mode');
    return response.data;
  },
};
