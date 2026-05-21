import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import toast from 'react-hot-toast';

interface Question {
  id: number;
  text: string;
  type: string;
  points: number;
  options?: { id: number; text: string }[];
}

interface TestData {
  user_test_id: number;
  test_id: number;
  title: string;
  description: string | null;
  time_limit: number | null;
  questions: Question[];
}

const TakeTestPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [test, setTest] = useState<TestData | null>(null);
  const [answers, setAnswers] = useState<{ [key: number]: any }>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    startTest();
  }, [id]);

  const startTest = async () => {
    try {
      const response = await apiClient.post(`/tests/${id}/start`);
      setTest(response.data);
      if (response.data.time_limit) {
        setTimeLeft(response.data.time_limit * 60);
      }
    } catch (error: any) {
      console.error('Error starting test:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при начале теста');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          if (prev === 0) autoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [timeLeft]);

  const autoSubmit = () => {
    toast.error('Время вышло! Ответы автоматически сохранены.');
    handleSubmit();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (questionId: number, value: any) => {
    setAnswers({ ...answers, [questionId]: value });
  };

  const handleSingleChoice = (questionId: number, optionId: number) => {
    setAnswers({ ...answers, [questionId]: optionId });
  };

  const handleMultipleChoice = (questionId: number, optionId: number, checked: boolean) => {
    const current = answers[questionId] || [];
    if (checked) {
      setAnswers({ ...answers, [questionId]: [...current, optionId] });
    } else {
      setAnswers({ ...answers, [questionId]: current.filter((id: number) => id !== optionId) });
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const formattedAnswers = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: parseInt(questionId),
        answer: Array.isArray(answer) ? JSON.stringify(answer) : String(answer)
      }));
      
      await apiClient.post(`/tests/submit/${test?.user_test_id}`, { answers: formattedAnswers });
      toast.success('Тест завершён!');
      navigate(`/test/${id}/result`);
    } catch (error) {
      console.error('Error submitting test:', error);
      toast.error('Ошибка при отправке теста');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка теста...</p>
      </div>
    );
  }

  if (!test) return null;

  const currentQuestion = test.questions[currentIndex];
  const isLast = currentIndex === test.questions.length - 1;
  const progress = ((currentIndex + 1) / test.questions.length) * 100;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-3xl">
        {/* Header */}
        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-white">{test.title}</h1>
              {test.description && (
                <p className="text-gray-400 mt-2">{test.description}</p>
              )}
            </div>
            {test.time_limit && (
              <div className="text-right">
                <div className="text-sm text-gray-400">Осталось времени</div>
                <div className={`text-2xl font-bold ${timeLeft && timeLeft < 60 ? 'text-red-500' : 'text-accent'}`}>
                  {timeLeft !== null ? formatTime(timeLeft) : '--:--'}
                </div>
              </div>
            )}
          </div>
          
          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-1">
              <span>Вопрос {currentIndex + 1} из {test.questions.length}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div className="bg-accent h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        </div>

        {/* Question */}
        <div className="bg-dark-card rounded-xl p-6 border border-white/10">
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-semibold text-white">Вопрос {currentIndex + 1}</h3>
              <span className="text-sm text-gray-400">{currentQuestion.points} баллов</span>
            </div>
            <p className="text-white text-lg">{currentQuestion.text}</p>
          </div>

          {/* Ответ в зависимости от типа вопроса */}
          <div className="mt-6">
            {currentQuestion.type === 'single' && currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((opt) => (
                  <label key={opt.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800 cursor-pointer hover:bg-gray-700 transition">
                    <input
                      type="radio"
                      name={`q${currentQuestion.id}`}
                      value={opt.id}
                      checked={answers[currentQuestion.id] === opt.id}
                      onChange={() => handleSingleChoice(currentQuestion.id, opt.id)}
                      className="w-4 h-4"
                    />
                    <span className="text-white">{opt.text}</span>
                  </label>
                ))}
              </div>
            )}

            {currentQuestion.type === 'multiple' && currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((opt) => (
                  <label key={opt.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800 cursor-pointer hover:bg-gray-700 transition">
                    <input
                      type="checkbox"
                      checked={(answers[currentQuestion.id] || []).includes(opt.id)}
                      onChange={(e) => handleMultipleChoice(currentQuestion.id, opt.id, e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="text-white">{opt.text}</span>
                  </label>
                ))}
              </div>
            )}

            {currentQuestion.type === 'number' && (
              <input
                type="number"
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white"
                placeholder="Введите число"
              />
            )}

            {currentQuestion.type === 'open' && (
              <textarea
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                rows={5}
                className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white"
                placeholder="Введите развёрнутый ответ..."
              />
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={() => setCurrentIndex(currentIndex - 1)}
              disabled={currentIndex === 0}
              className="px-6 py-2 rounded-lg border border-white/20 text-white hover:bg-white/10 transition disabled:opacity-50"
            >
              ← Назад
            </button>
            
            {isLast ? (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
              >
                {submitting ? 'Отправка...' : 'Завершить тест'}
              </button>
            ) : (
              <button
                onClick={() => setCurrentIndex(currentIndex + 1)}
                className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition"
              >
                Далее →
              </button>
            )}
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TakeTestPage;