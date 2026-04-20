import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import apiClient from '../api/client';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Недействительная ссылка подтверждения');
        return;
      }

      try {
        const response = await apiClient.get(`/auth/verify-email?token=${token}`);
        setStatus('success');
        setMessage(response.data.message);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } catch (error: any) {
        setStatus('error');
        setMessage(error.response?.data?.detail || 'Ошибка подтверждения email');
      }
    };

    verify();
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-[#0a0f0a] dark:to-[#0d1b12]">
      <div className="bg-white dark:bg-[#1a1a1a] rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <div className="text-6xl mb-4">⏳</div>
            <h2 className="text-2xl font-bold mb-2 dark:text-white">Подтверждение...</h2>
            <p className="text-gray-600 dark:text-gray-400">Пожалуйста, подождите</p>
            <div className="mt-4 animate-spin rounded-full h-8 w-8 border-b-2 border-[#2e7d5e] mx-auto"></div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold mb-2 text-green-600 dark:text-green-400">Email подтверждён!</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>
            <p className="text-sm text-gray-500 dark:text-gray-500">Перенаправление на страницу входа...</p>
            <Link to="/login" className="inline-block mt-4 text-[#2e7d5e] hover:underline">
              Перейти сейчас
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-6xl mb-4">❌</div>
            <h2 className="text-2xl font-bold mb-2 text-red-600 dark:text-red-400">Ошибка подтверждения</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>
            <Link to="/login" className="inline-block mt-2 text-[#2e7d5e] hover:underline">
              Перейти ко входу
            </Link>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
