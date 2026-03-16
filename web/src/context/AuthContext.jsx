import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!token);

  const fetchUser = useCallback(async () => {
    if (!token) { setUser(null); setLoading(false); return; }
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchUser(); }, [fetchUser]);

  const login = (jwt) => {
    localStorage.setItem('token', jwt);
    setToken(jwt);
    setLoading(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = () => fetchUser();

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
