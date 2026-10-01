import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';

const Register: React.FC = () => {
  const [searchParams] = useSearchParams();
  const inviteCode = searchParams.get('invite');

  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher'>(
    inviteCode ? 'student' : 'teacher'
  );
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const { register, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      if (inviteCode) {
        navigate(`/join?invite=${inviteCode}`, { replace: true });
      } else {
        navigate('/dashboard');
      }
    }
  }, [user, navigate, inviteCode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    if (password.length < 6) {
      setError('Пароль должен быть не менее 6 символов');
      return;
    }
    if (role === 'student' && !inviteCode) {
      setError('Регистрация ученика возможна только по приглашению');
      return;
    }

    try {
      await register(email, fullName, password, role, inviteCode || undefined);
      setSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Ошибка регистрации. Попробуйте другой email.'
      );
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
              ✅ Регистрация успешна!
              {role === 'student'
                ? ' Вы привязаны к репетитору.'
                : ' Теперь вы можете войти в свой аккаунт.'}
              <br />
              <Link to="/login" className="text-accent hover:underline mt-2 inline-block">
                Перейти ко входу
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-4 p-3 rounded-lg bg-danger/20 text-danger text-sm text-center">
                  {error}
                </div>
              )}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Полное имя
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Пароль</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Подтвердите пароль
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Кто вы?</label>

                  {inviteCode ? (
                    <div className="p-3 rounded-lg bg-accent/20 border border-accent/40">
                      <p className="text-sm text-accent">
                        🧑‍🎓 Вы регистрируетесь как <strong>Ученик</strong> по приглашению
                        репетитора.
                      </p>
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-gray-800 border border-gray-700">
                      <p className="text-sm text-gray-300">
                        👨‍🏫 Вы регистрируетесь как <strong>Репетитор</strong>.
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Ученики регистрируются только по ссылке-приглашению от репетитора.
                      </p>
                    </div>
                  )}
                </div>

                <button type="submit" className="btn-primary w-full">
                  Зарегистрироваться
                </button>
              </form>
              <p className="text-center text-sm text-gray-400 mt-6">
                Уже есть аккаунт?{' '}
                <Link to="/login" className="text-accent hover:underline">
                  Войти
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default Register;