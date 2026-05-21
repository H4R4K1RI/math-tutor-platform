import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiArrowLeft, FiCheckCircle, FiClock, FiXCircle, FiTrendingUp } from 'react-icons/fi';

interface AssignmentStats {
  id: number;
  title: string;
  due_date: string;
  status: 'not_submitted' | 'pending' | 'approved' | 'rejected';
  feedback: string | null;
  grade: string | null;
}

interface StudentStats {
  student: {
    id: number;
    name: string;
    email: string;
    registered_at: string;
  };
  stats: {
    total_assignments: number;
    completed: number;
    pending: number;
    rejected: number;
    progress: number;
  };
  assignments: AssignmentStats[];
}

const StudentStatsPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isTeacher } = useAuth();
  const [stats, setStats] = useState<StudentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isTeacher) return;
    fetchStats();
  }, [id, isTeacher]);

  const fetchStats = async () => {
    try {
      const response = await apiClient.get(`/students/${id}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching student stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">✅ Зачтено</span>;
      case 'rejected':
        return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">❌ На доработку</span>;
      case 'pending':
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">⏳ Ожидает</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400">📋 Не сдано</span>;
    }
  };

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка статистики...</p>
      </div>
    );
  }

  if (!stats) {
    return <div className="text-center py-20 text-white">Ученик не найден</div>;
  }

  const { student, stats: studentStats, assignments } = stats;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        {/* Кнопка назад */}
        <button
          onClick={() => navigate('/students')}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition mb-6"
        >
          <FiArrowLeft size={20} />
          <span>Назад к ученикам</span>
        </button>

        {/* Информация об ученике */}
        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-2xl text-accent font-bold">
                {student.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{student.name}</h1>
              <p className="text-gray-400">{student.email}</p>
              <p className="text-sm text-gray-500 mt-1">
                Зарегистрирован: {new Date(student.registered_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Карточки статистики */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <FiTrendingUp className="mx-auto mb-2 text-accent" size={24} />
            <div className="text-2xl font-bold text-white">{studentStats.total_assignments}</div>
            <div className="text-sm text-gray-400">Всего заданий</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <FiCheckCircle className="mx-auto mb-2 text-green-400" size={24} />
            <div className="text-2xl font-bold text-white">{studentStats.completed}</div>
            <div className="text-sm text-gray-400">Зачтено</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <FiClock className="mx-auto mb-2 text-yellow-400" size={24} />
            <div className="text-2xl font-bold text-white">{studentStats.pending}</div>
            <div className="text-sm text-gray-400">Ожидают</div>
          </div>
          <div className="bg-dark-card rounded-xl p-4 text-center border border-white/10">
            <FiXCircle className="mx-auto mb-2 text-red-400" size={24} />
            <div className="text-2xl font-bold text-white">{studentStats.rejected}</div>
            <div className="text-sm text-gray-400">На доработку</div>
          </div>
        </div>

        {/* Прогресс-бар */}
        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Общий прогресс</span>
            <span>{studentStats.progress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className="bg-accent h-3 rounded-full transition-all duration-500"
              style={{ width: `${studentStats.progress}%` }}
            />
          </div>
        </div>

        {/* Список заданий */}
        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold text-white">История заданий</h2>
          </div>
          <div className="divide-y divide-white/10">
            {assignments.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                Нет заданий
              </div>
            ) : (
              assignments.map((assignment) => (
                <div key={assignment.id} className="p-4 hover:bg-white/5 transition">
                  <div className="flex justify-between items-start flex-wrap gap-2">
                    <div>
                      <h3 className="font-medium text-white">{assignment.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        📅 Дедлайн: {new Date(assignment.due_date).toLocaleDateString()}
                      </p>
                      {assignment.feedback && (
                        <p className="text-sm text-gray-400 mt-2">
                          💬 Фидбек: {assignment.feedback}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(assignment.status)}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default StudentStatsPage;