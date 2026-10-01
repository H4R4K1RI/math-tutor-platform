import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { User } from '../types';
import { initSocket, connectSocket, disconnectSocket, socket } from '../socket';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, full_name: string, password: string, role: string, invite_code?: string) => Promise<void>;
  logout: () => Promise<void>;
  isTeacher: boolean;
  isLoading: boolean;
  refreshUser: () => Promise<void>;
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
  const isLoggingOut = React.useRef(false);
  const navigate = useNavigate();

  const fetchUser = async () => {
    if (isLoggingOut.current) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
      if (!socket) initSocket();
      connectSocket();
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  // Слушаем событие "auth:expired" от axios-интерцептора
  useEffect(() => {
    const handleAuthExpired = () => {
      setUser(null);
      disconnectSocket();
      navigate('/login', { replace: true });
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, [navigate]);

  const login = async (email: string, password: string) => {
    isLoggingOut.current = false;
    await apiClient.post('/auth/login', { email, password });
    await fetchUser();
  };

  const register = async (
    email: string,
    full_name: string,
    password: string,
    role: string,
    invite_code?: string
  ) => {
    await apiClient.post('/auth/register', {
      email,
      full_name,
      password,
      role,
      invite_code: invite_code || null,
    });
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
    window.location.href = '/login';
  };

  const isTeacher = user?.role === 'teacher';

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isTeacher, isLoading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};