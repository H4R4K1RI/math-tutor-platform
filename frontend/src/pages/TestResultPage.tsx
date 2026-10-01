import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiCheckCircle, FiXCircle } from 'react-icons/fi';

interface AnswerResult {
  question_id: number;
  question_text: string;
  user_answer: string;
  is_correct: boolean;
  points_earned: number;
  max_points: number;
}

interface TestResult {
  score: number;
  max_score: number;
  passed: boolean;
  passing_score: number;
  started_at: string;
  finished_at: string;
  answers: AnswerResult[];
}

const TestResultPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchResult();
  }, [id]);

  const fetchResult = async () => {
    try {
      const response = await apiClient.get(`/tests/student/${id}`);
      setResult(response.data);
    } catch (error) {
      console.error('Error fetching result:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка результатов...</p>
      </div>
    );
  }

  if (!result) return null;

  const startDate = new Date(result.started_at);
  const finishDate = new Date(result.finished_at);
  const duration = Math.round((finishDate.getTime() - startDate.getTime()) / 1000 / 60);

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="bg-dark-card rounded-xl p-8 border border-white/10 text-center mb-6">
          {result.passed ? (
            <FiCheckCircle className="mx-auto text-green-500" size={64} />
          ) : (
            <FiXCircle className="mx-auto text-red-500" size={64} />
          )}
          <h1 className="text-2xl font-bold text-white mt-4">
            {result.passed ? 'Поздравляем!' : 'Тест не пройден'}
          </h1>
          <p className="text-gray-400 mt-2">
            Ваш результат: {result.score}% (проходной балл: {result.passing_score}%)
          </p>
          <div className="mt-4 w-full bg-gray-700 rounded-full h-3 max-w-md mx-auto">
            <div
              className={`h-3 rounded-full transition-all ${result.passed ? 'bg-green-500' : 'bg-red-500'}`}
              style={{ width: `${result.score}%` }}
            />
          </div>
          <p className="text-gray-500 text-sm mt-4">
            Набрано баллов: {result.score} из {result.max_score}
          </p>
          <p className="text-gray-500 text-sm">
            Время выполнения: {duration} мин
          </p>
        </div>

        <h2 className="text-xl font-semibold text-white mb-4">Детальные результаты</h2>
        <div className="space-y-3">
          {result.answers.map((ans, idx) => (
            <div key={idx} className="bg-dark-card rounded-xl p-4 border border-white/10">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-white font-medium">{ans.question_text}</p>
                  <p className="text-gray-400 text-sm mt-1">
                    Ваш ответ: <span className="text-accent">{ans.user_answer || '(не указан)'}</span>
                  </p>
                </div>
                <div className="text-right">
                  {ans.is_correct ? (
                    <FiCheckCircle className="text-green-500" size={20} />
                  ) : (
                    <FiXCircle className="text-red-500" size={20} />
                  )}
                  <p className="text-sm text-gray-400 mt-1">
                    {ans.points_earned}/{ans.max_points} баллов
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition"
          >
            На главную
          </button>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TestResultPage;