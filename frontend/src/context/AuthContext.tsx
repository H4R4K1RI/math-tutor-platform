import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
import apiClient from '../api/client';
import { User } from '../types';
import { initSocket, connectSocket, disconnectSocket, socket } from '../socket';

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
  const isLoggingOut = useRef(false);

  const fetchUser = async () => {
    // Если мы выходим - не делаем запрос
    if (isLoggingOut.current) {
      setIsLoading(false);
      return;
    }
    
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
      
      // Подключаем Socket.IO если пользователь авторизован
      if (!socket) initSocket();
      connectSocket();
      
    } catch (error: any) {
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
    isLoggingOut.current = true;
    setUser(null);
    disconnectSocket();
    
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }

    document.cookie.split(";").forEach(function(c) {
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
  });
    
    window.location.href = '/login';
  };

  const isTeacher = user?.role === 'teacher';

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isTeacher, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
