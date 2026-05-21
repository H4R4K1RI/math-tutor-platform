import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiPlus, FiEdit2, FiTrash2, FiEye, FiClock, FiFileText } from 'react-icons/fi';
import toast from 'react-hot-toast';

interface Test {
  id: number;
  title: string;
  description: string | null;
  time_limit: number | null;
  passing_score: number;
  is_active: boolean;
  created_at: string;
  questions_count: number;
}

const TestsPage: React.FC = () => {
  const { isTeacher } = useAuth();
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isTeacher) return;
    fetchTests();
  }, [isTeacher]);

  const fetchTests = async () => {
    try {
      const response = await apiClient.get('/tests');
      setTests(response.data);
    } catch (error) {
      console.error('Error fetching tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteTest = async (id: number) => {
    if (!confirm('Удалить тест? Все результаты будут потеряны.')) return;
    try {
      await apiClient.delete(`/tests/${id}`);
      toast.success('Тест удалён');
      fetchTests();
    } catch (error) {
      console.error('Error deleting test:', error);
      toast.error('Ошибка при удалении');
    }
  };

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

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
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Тесты</h1>
          <Link
            to="/tests/new"
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
          >
            <FiPlus size={18} />
            <span>Создать тест</span>
          </Link>
        </div>

        {tests.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiFileText size={48} className="mx-auto mb-4 opacity-50" />
            <p>У вас пока нет тестов</p>
            <p className="text-sm">Нажмите "Создать тест", чтобы начать</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tests.map((test) => (
              <div
                key={test.id}
                className="bg-dark-card rounded-xl p-5 border border-white/10 hover:border-accent transition-all duration-200"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-semibold text-white text-lg flex-1">{test.title}</h3>
                  <div className="flex gap-2">
                    <Link
                      to={`/tests/${test.id}/edit`}
                      className="text-gray-400 hover:text-accent transition"
                      title="Редактировать"
                    >
                      <FiEdit2 size={16} />
                    </Link>
                    <button
                      onClick={() => deleteTest(test.id)}
                      className="text-gray-400 hover:text-red-400 transition"
                      title="Удалить"
                    >
                      <FiTrash2 size={16} />
                    </button>
                  </div>
                </div>
                
                {test.description && (
                  <p className="text-gray-400 text-sm mb-3 line-clamp-2">{test.description}</p>
                )}
                
                <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                  <div className="flex items-center gap-1">
                    <FiFileText size={14} />
                    <span>{test.questions_count} вопросов</span>
                  </div>
                  {test.time_limit && (
                    <div className="flex items-center gap-1">
                      <FiClock size={14} />
                      <span>{test.time_limit} мин</span>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
                  <span className={`text-xs px-2 py-1 rounded-full ${test.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {test.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                  <Link
                    to={`/tests/${test.id}/results`}
                    className="text-accent hover:text-accent/80 transition flex items-center gap-1 text-sm"
                  >
                    <FiEye size={14} />
                    <span>Результаты</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default TestsPage;