import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';

const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const { register, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/dashboard');
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    try {
      await register(email, fullName, password);
      setSuccess(true);
    } catch (err) {
      setError('Ошибка регистрации. Попробуйте другой email.');
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="bg-dark-card rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/10 fade-in">
          <h2 className="text-3xl font-bold text-center text-white mb-2">Регистрация</h2>
          <p className="text-center text-gray-400 mb-6">Создайте новый аккаунт</p>

          {success ? (
            <div className="mb-4 p-3 rounded-lg bg-green-900/50 text-green-400 text-sm text-center">
              ✅ Регистрация успешна! На вашу почту отправлена ссылка для подтверждения.
              <br />
              <Link to="/login" className="text-accent hover:underline mt-2 inline-block">Перейти ко входу</Link>
            </div>
          ) : (
            <>
              {error && <div className="mb-4 p-3 rounded-lg bg-danger/20 text-danger text-sm text-center">{error}</div>}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Полное имя</label>
                  <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="input" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Пароль</label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Подтвердите пароль</label>
                  <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input" required />
                </div>
                <button type="submit" className="btn-primary w-full">Зарегистрироваться</button>
              </form>
              <p className="text-center text-sm text-gray-400 mt-6">
                Уже есть аккаунт? <Link to="/login" className="text-accent hover:underline">Войти</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default Register;