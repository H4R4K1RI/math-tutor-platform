import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/dashboard');
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail === 'Email not verified' ? 'Email не подтверждён. Проверьте почту.' : (detail || 'Неверный email или пароль'));
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="bg-dark-card rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/10 fade-in">
          <h2 className="text-3xl font-bold text-center text-white mb-2">Добро пожаловать</h2>
          <p className="text-center text-gray-400 mb-6">Войдите в свой аккаунт</p>
          {error && <div className="mb-4 p-3 rounded-lg bg-danger/20 text-danger text-sm text-center">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Пароль</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" required />
            </div>
            <button type="submit" className="btn-primary w-full">Войти</button>
          </form>
          <p className="text-center text-sm text-gray-400 mt-6">
            Нет аккаунта? <Link to="/register" className="text-accent hover:underline">Зарегистрироваться</Link>
          </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default Login;