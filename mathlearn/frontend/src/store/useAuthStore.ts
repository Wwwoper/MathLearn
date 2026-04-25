import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  name: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    localStorage.setItem('access_token', token);
    set({ token });
  },
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, token: null });
  },
}));
