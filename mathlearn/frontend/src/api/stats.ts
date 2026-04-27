import apiClient from './client';

export interface HeatmapCell {
  factor_a: number;
  factor_b: number;
  error_count: number;
  avg_time_ms: number;
  accuracy: number;
}

export interface HeatmapResponse {
  matrix: HeatmapCell[][];
}

export interface SpeedDataPoint {
  date: string;
  avg_response_ms: number;
  accuracy: number;
}

export interface SpeedResponse {
  data_points: SpeedDataPoint[];
  days: number;
}

export interface StreakResponse {
  current_streak: number;
  max_streak: number;
}

export interface AchievementResponse {
  id: number;
  name: string;
  description: string;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface AchievementsResponse {
  achievements: AchievementResponse[];
}

export const statsApi = {
  getHeatmap: async (): Promise<HeatmapResponse> => {
    const response = await apiClient.get('/stats/heatmap');
    return response.data;
  },

  getSpeed: async (days: number = 30): Promise<SpeedResponse> => {
    const response = await apiClient.get(`/stats/speed?days=${days}`);
    return response.data;
  },

  getStreak: async (): Promise<StreakResponse> => {
    const response = await apiClient.get('/stats/streak');
    return response.data;
  },

  getAchievements: async (): Promise<AchievementsResponse> => {
    const response = await apiClient.get('/stats/achievements');
    return response.data;
  },
};
