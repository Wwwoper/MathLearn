import { create } from 'zustand';
import type { LearningMode } from '../components/LearningModeSelector/LearningModeSelector';

interface User {
  id: number;
  email: string;
  name: string;
  learning_mode?: LearningMode;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
  updateUserLearningMode: (mode: LearningMode) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  setUser: (user) => {
    console.log('Setting user:', user);
    set({ user });
  },
  setToken: (token) => {
    console.log('Setting token and saving to localStorage');
    localStorage.setItem('access_token', token);
    set({ token });
  },
  logout: () => {
    console.log('Logging out');
    localStorage.removeItem('access_token');
    set({ user: null, token: null });
  },
  updateUserLearningMode: (mode: LearningMode) => {
    const currentUser = get().user;
    if (currentUser) {
      set({ user: { ...currentUser, learning_mode: mode } });
    }
  },
}));
