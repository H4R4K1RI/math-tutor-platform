import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiArrowLeft, FiCheckCircle, FiXCircle } from 'react-icons/fi';

interface AnswerResult {
  question_id: number;
  question_text: string;
  user_answer: string;
  is_correct: boolean;
  points_earned: number;
  max_points: number;
  options?: { id: number; text: string; is_correct: boolean }[];
}

interface TestResult {
  student_id: number;
  score: number;
  max_score: number;
  total_earned: number;
  passed: boolean;
  started_at: string;
  finished_at: string;
  answers: AnswerResult[];
}

const TestStudentResultPage: React.FC = () => {
  const { testId, userId } = useParams();
  const navigate = useNavigate();
  const { isTeacher } = useAuth();
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isTeacher) return;
    fetchResult();
  }, [testId, userId]);

  const fetchResult = async () => {
    try {
      const response = await apiClient.get(`/tests/${testId}/results/${userId}`);
      setResult(response.data);
    } catch (error) {
      console.error('Error fetching result:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAnswerText = (answer: AnswerResult) => {
    if (!answer.user_answer) return '(не указан)';
    
    // Если есть варианты ответов
    if (answer.options && answer.options.length > 0) {
      try {
        const answerIds = JSON.parse(answer.user_answer);
        if (Array.isArray(answerIds)) {
          const selectedTexts = answerIds.map((id: number) => {
            const opt = answer.options?.find((o) => o.id === id);
            return opt ? opt.text : id;
          });
          return selectedTexts.join(', ');
        } else {
          const opt = answer.options?.find((o) => o.id === parseInt(answer.user_answer));
          return opt ? opt.text : answer.user_answer;
        }
      } catch {
        return answer.user_answer;
      }
    }
    
    return answer.user_answer;
  };

  if (!isTeacher) return <div className="text-center py-20 text-white">Доступ только для учителей</div>;

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (!result) return <div className="text-center py-20 text-white">Результат не найден</div>;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <button 
          onClick={() => navigate(`/tests/${testId}/results`)} 
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6"
        >
          <FiArrowLeft size={20} /> Назад к результатам
        </button>

        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <h1 className="text-2xl font-bold text-white">Результат ученика</h1>
          <p className={`mt-2 ${result.passed ? 'text-green-400' : 'text-red-400'}`}>
            Оценка: {result.score}% ({result.passed ? 'Зачтено' : 'Не зачтено'})
          </p>
          <p className="text-gray-400 mt-1">
            Набрано баллов: {result.total_earned} из {result.max_score}
          </p>
        </div>

        <div className="space-y-3">
          {result.answers.map((ans, idx) => (
            <div key={idx} className="bg-dark-card rounded-xl p-4 border border-white/10">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-white font-medium">{ans.question_text}</p>
                  <p className="text-gray-400 text-sm mt-1">
                    Ответ ученика: {getAnswerText(ans)}
                  </p>
                </div>
                <div className="text-right">
                  {ans.is_correct ? 
                    <FiCheckCircle className="text-green-500" size={20} /> : 
                    <FiXCircle className="text-red-500" size={20} />
                  }
                  <p className="text-sm text-gray-400 mt-1">
                    {ans.points_earned}/{ans.max_points} баллов
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TestStudentResultPage;