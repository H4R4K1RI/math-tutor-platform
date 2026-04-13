import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Неверный email или пароль');
      }
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-[#0a0f0a] dark:to-[#0d1b12] overflow-hidden">
      <div className="bg-white/80 dark:bg-[#1a1a1a]/80 backdrop-blur-sm rounded-2xl shadow-xl p-6 w-full max-w-md border border-gray-200 dark:border-gray-700">
        <h2 className="text-2xl font-bold text-center text-gray-800 dark:text-white mb-2">Добро пожаловать</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-6">Войдите в свой аккаунт</p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#2e7d5e] focus:border-transparent bg-white dark:bg-[#2a2a2a] text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#2e7d5e] focus:border-transparent bg-white dark:bg-[#2a2a2a] text-gray-900 dark:text-white"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full border border-[#2e7d5e] text-[#2e7d5e] hover:bg-[#2e7d5e] hover:text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 bg-transparent"
          >
            Войти
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 dark:text-gray-400 mt-6">
          Нет аккаунта?{' '}
          <Link to="/register" className="text-[#2e7d5e] dark:text-[#4a9b6e] hover:underline font-medium">
            Зарегистрироваться
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;