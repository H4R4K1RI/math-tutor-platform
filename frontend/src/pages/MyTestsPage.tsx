import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiClock, FiFileText, FiCheckCircle } from 'react-icons/fi';

interface Test {
  id: number;
  title: string;
  description: string | null;
  time_limit: number | null;
  passing_score: number;
  is_completed?: boolean;
  score?: number;
  passed?: boolean;
}

const MyTestsPage: React.FC = () => {
  const { user } = useAuth();
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    fetchTests();
  }, [user]);

  const fetchTests = async () => {
    try {
      // Получаем тесты, назначенные ученику
      const response = await apiClient.get('/tests/assigned');
      setTests(response.data);
    } catch (error) {
      console.error('Error fetching tests:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка тестов...</p>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <h1 className="text-2xl font-bold text-white mb-6">Мои тесты</h1>

        {tests.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiFileText size={48} className="mx-auto mb-4 opacity-50" />
            <p>У вас пока нет назначенных тестов</p>
          </div>
        ) : (
          <div className="space-y-4">
            {tests.map((test) => (
              <div
                key={test.id}
                className="bg-dark-card rounded-xl p-5 border border-white/10 hover:border-accent transition-all duration-200"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-white text-lg">{test.title}</h3>
                    {test.description && (
                      <p className="text-gray-400 text-sm mt-1">{test.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      {test.time_limit && (
                        <div className="flex items-center gap-1">
                          <FiClock size={14} />
                          <span>{test.time_limit} минут</span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <FiCheckCircle size={14} />
                        <span>Проходной балл: {test.passing_score}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    {test.is_completed ? (
                      <div className="text-center">
                        <span className={`text-sm font-semibold ${test.passed ? 'text-green-400' : 'text-red-400'}`}>
                          {test.passed ? '✅ Зачтено' : '❌ Не зачтено'}
                        </span>
                        <div className="text-sm text-gray-400 mt-1">
                          Результат: {test.score}%
                        </div>
                        <Link
                          to={`/test/${test.id}/result`}
                          className="inline-block mt-2 text-accent hover:underline text-sm"
                        >
                          Посмотреть результат
                        </Link>
                      </div>
                    ) : (
                      <Link
                        to={`/test/${test.id}`}
                        className="inline-block px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition"
                      >
                        Начать тест
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default MyTestsPage;