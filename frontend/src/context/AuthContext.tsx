import React, { createContext, useState, useContext, useEffect } from 'react';
import apiClient from '../api/client';
import { User, AuthResponse } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, full_name: string, password: string) => Promise<void>;
  logout: () => void;
  isTeacher: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));

  useEffect(() => {
    if (token) {
      apiClient.get('/auth/me').then(response => {
        setUser(response.data);
      }).catch(() => {
        logout();
      });
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<AuthResponse>('/auth/login', { email, password });
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    
    const userResponse = await apiClient.get<User>('/auth/me');
    setUser(userResponse.data);
  };

  const register = async (email: string, full_name: string, password: string) => {
    await apiClient.post('/auth/register', { email, full_name, password });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const isTeacher = user?.role === 'teacher';

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isTeacher }}>
      {children}
    </AuthContext.Provider>
  );
};