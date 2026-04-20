import React, { createContext, useState, useContext, useEffect } from 'react';
import apiClient from '../api/client';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, full_name: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isTeacher: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email: string, password: string) => {
    await apiClient.post('/auth/login', { email, password });
    await fetchUser();
  };

  const register = async (email: string, full_name: string, password: string) => {
    await apiClient.post('/auth/register', { email, full_name, password });
  };

  const logout = async () => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem('access_token');
    setUser(null);
    // Принудительно перенаправляем на страницу входа
    window.location.href = '/login';
  }
};

  const isTeacher = user?.role === 'teacher';

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isTeacher, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
