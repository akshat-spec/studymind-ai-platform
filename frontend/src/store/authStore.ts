import { create } from 'zustand'
import axios from 'axios'

interface User {
  id: string
  email: string
  full_name: string | null
  plan: string
  usage?: Record<string, { used: number, limit: number | null, is_unlimited: boolean }>
}

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  setAuth: (user, token) => set({ user, accessToken: token, isAuthenticated: true }),
  clearAuth: () => set({ user: null, accessToken: null, isAuthenticated: false }),
  checkAuth: async () => {
    const token = get().accessToken;
    if (!token) return;
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      set({ user: res.data });
    } catch (e) {
      console.error("Check auth failed", e);
    }
  }
}))
