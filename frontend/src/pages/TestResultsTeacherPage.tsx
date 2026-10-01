import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiArrowLeft, FiUser, FiCheckCircle, FiXCircle } from 'react-icons/fi';

interface StudentResult {
  user_test_id: number;
  student_id: number;
  student_name: string;
  score: number;
  max_score: number;
  passed: boolean;
  started_at: string;
  finished_at: string;
}

interface TestStatistics {
  total_attempts: number;
  passed: number;
  passed_percent: number;
  average_score: number;
}

interface TestData {
  test: {
    id: number;
    title: string;
    passing_score: number;
  };
  statistics: TestStatistics;
  results: StudentResult[];
}

const TestResultsTeacherPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isTeacher } = useAuth();
  const [data, setData] = useState<TestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isTeacher) return;
    fetchResults();
  }, [id, isTeacher]);

  const fetchResults = async () => {
    try {
      const response = await apiClient.get(`/tests/results/${id}`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка результатов...</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <button
          onClick={() => navigate('/tests')}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition mb-6"
        >
          <FiArrowLeft size={20} />
          <span>Назад к тестам</span>
        </button>

        <h1 className="text-2xl font-bold text-white mb-2">{data.test.title}</h1>
        <p className="text-gray-400 mb-6">Проходной балл: {data.test.passing_score}%</p>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <div className="text-2xl font-bold text-white">{data.statistics.total_attempts}</div>
            <div className="text-sm text-gray-400">Всего попыток</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <div className="text-2xl font-bold text-green-400">{data.statistics.passed}</div>
            <div className="text-sm text-gray-400">Зачтено</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <div className="text-2xl font-bold text-white">{data.statistics.passed_percent}%</div>
            <div className="text-sm text-gray-400">Успеваемость</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <div className="text-2xl font-bold text-white">{data.statistics.average_score}%</div>
            <div className="text-sm text-gray-400">Средний балл</div>
          </div>
        </div>

        {/* Таблица результатов — кликабельные строки */}
        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold text-white">Результаты учеников</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Ученик</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-400">Результат</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-400">Статус</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Дата</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {data.results.map((result) => (
                  <tr 
                    key={result.user_test_id} 
                    onClick={() => navigate(`/tests/${data.test.id}/results/${result.student_id}`)}
                    className="hover:bg-white/5 transition cursor-pointer"
                  >
                    <td className="px-4 py-3 text-white">
                      <div className="flex items-center gap-2">
                        <FiUser size={14} className="text-gray-400" />
                        {result.student_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-white">
                      {result.score}%
                    </td>
                    <td className="px-4 py-3 text-center">
                      {result.passed ? (
                        <span className="inline-flex items-center gap-1 text-green-400 text-sm">
                          <FiCheckCircle size={14} /> Зачтено
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-red-400 text-sm">
                          <FiXCircle size={14} /> Не зачтено
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400 text-sm">
                      {new Date(result.finished_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TestResultsTeacherPage;