import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import toast from 'react-hot-toast';
import { FiUserPlus, FiXCircle, FiCheckCircle } from 'react-icons/fi';

interface InviteInfo {
  valid: boolean;
  teacher_id: number;
  teacher_name: string;
}

const JoinByInvite: React.FC = () => {
  const [searchParams] = useSearchParams();
  const code = searchParams.get('invite');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [joining, setJoining] = useState(false);
  const [joined, setJoined] = useState(false);

  useEffect(() => {
    if (!code) {
      setError('Код приглашения не указан');
      setLoading(false);
      return;
    }
    validateInvite();
  }, [code]);

  const validateInvite = async () => {
    try {
      const response = await apiClient.post(`/invitations/validate/${code}`);
      setInviteInfo(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Недействительное приглашение');
    } finally {
      setLoading(false);
    }
  };

  const acceptInvite = async () => {
    if (!code) return;
    setJoining(true);
    try {
      await apiClient.post(`/invitations/accept/${code}`);
      setJoined(true);
      toast.success('Вы присоединились к репетитору!');
      setTimeout(() => navigate('/chats'), 2000);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при принятии приглашения');
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p>Проверка приглашения...</p>
        </div>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="min-h-screen flex items-center justify-center bg-dark-bg px-4">
        <div className="bg-dark-card rounded-2xl shadow-2xl p-8 w-full max-w-md border border-white/10">
          {error && (
            <>
              <div className="text-center mb-4">
                <FiXCircle className="mx-auto text-red-500 mb-2" size={48} />
                <h2 className="text-2xl font-bold text-white mb-2">Ошибка</h2>
                <p className="text-gray-400">{error}</p>
              </div>
              <Link
                to="/dashboard"
                className="block text-center text-accent hover:underline mt-4"
              >
                ← Вернуться на главную
              </Link>
            </>
          )}

          {!error && joined && (
            <div className="text-center">
              <FiCheckCircle className="mx-auto text-green-500 mb-2" size={48} />
              <h2 className="text-2xl font-bold text-white mb-2">
                Готово!
              </h2>
              <p className="text-gray-400">
                Вы присоединились к репетитору {inviteInfo?.teacher_name}.
                Перенаправление в чаты...
              </p>
            </div>
          )}

          {!error && !joined && inviteInfo && (
            <>
              <div className="text-center mb-6">
                <FiUserPlus className="mx-auto text-accent mb-2" size={48} />
                <h2 className="text-2xl font-bold text-white mb-2">
                  Приглашение на обучение
                </h2>
                <p className="text-gray-400">
                  Репетитор <strong className="text-white">{inviteInfo.teacher_name}</strong>{' '}
                  приглашает вас на обучение.
                </p>
              </div>

              {!user ? (
                <>
                  <p className="text-sm text-gray-400 text-center mb-4">
                    Войдите в аккаунт, чтобы принять приглашение. Если у вас ещё
                    нет аккаунта — зарегистрируйтесь как ученик.
                  </p>
                  <div className="space-y-3">
                    <Link
                      to={`/login?redirect=${encodeURIComponent(`/join?invite=${code}`)}`}
                      className="block w-full text-center px-4 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition"
                    >
                      Войти и принять приглашение
                    </Link>
                    <Link
                      to={`/register?invite=${code}`}
                      className="block w-full text-center px-4 py-3 rounded-lg border border-white/20 text-white hover:bg-white/10 transition"
                    >
                      Зарегистрироваться как ученик
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  <div className="p-3 rounded-lg bg-gray-800 mb-4 text-sm text-gray-300">
                    Вы вошли как <strong className="text-white">{user.full_name}</strong>{' '}
                    ({user.email})
                  </div>
                  <button
                    onClick={acceptInvite}
                    disabled={joining}
                    className="w-full px-4 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition disabled:opacity-50"
                  >
                    {joining ? 'Присоединяемся...' : 'Присоединиться к репетитору'}
                  </button>
                </>
              )}

              <Link
                to="/dashboard"
                className="block text-center text-gray-500 hover:text-gray-400 mt-4 text-sm"
              >
                Отмена
              </Link>
            </>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default JoinByInvite;