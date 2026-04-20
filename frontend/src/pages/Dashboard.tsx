import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Assignment, Submission } from '../types';
import { Link } from 'react-router-dom';
import { SkeletonCard } from '../components/Skeleton';
import AnimatedPage from '../components/AnimatedPage';
import { socket } from '../socket';
import { FiBookOpen, FiCheckCircle, FiClock, FiMessageCircle, FiTrendingUp, FiAward } from 'react-icons/fi';

const Dashboard: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  const fetchData = async () => {
    try {
      const [assignmentsRes, submissionsRes] = await Promise.all([
        apiClient.get('/assignments'),
        apiClient.get('/submissions')
      ]);
      
      const assignmentsData = assignmentsRes.data.items || assignmentsRes.data;
      const submissionsData = submissionsRes.data.items || submissionsRes.data;
      
      setAssignments(assignmentsData);
      setSubmissions(submissionsData);
      
      // Подсчет статистики для ученика
      if (!isTeacher) {
        const pending = submissionsData.filter((s: Submission) => s.status === 'pending').length;
        const approved = submissionsData.filter((s: Submission) => s.status === 'approved').length;
        const rejected = submissionsData.filter((s: Submission) => s.status === 'rejected').length;
        
        setStats({
          total: submissionsData.length,
          pending,
          approved,
          rejected
        });
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // WebSocket обновления
  useEffect(() => {
    const handleUpdate = () => {
      fetchData();
    };
    
    if (socket) {
      socket.on('assignment_updated', handleUpdate);
      socket.on('submission_updated', handleUpdate);
      socket.on('assignment_deleted', handleUpdate);
    }
    
    return () => {
      if (socket) {
        socket.off('assignment_updated', handleUpdate);
        socket.off('submission_updated', handleUpdate);
        socket.off('assignment_deleted', handleUpdate);
      }
    };
  }, []);

  if (loading) {
    return (
      <AnimatedPage>
        <div className="container mx-auto px-4 py-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </div>
      </AnimatedPage>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Приветствие */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Добро пожаловать, {user?.full_name?.split(' ')[0]}!
          </h1>
          <p className="text-gray-400">Рады видеть вас на платформе</p>
        </div>
        
        {isTeacher ? (
          // ========== ВИД ДЛЯ УЧИТЕЛЯ ==========
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Статистика */}
            <div className="gradient-border p-6">
              <div className="flex items-center gap-3 mb-4">
                <FiTrendingUp size={24} className="text-accent" />
                <h2 className="text-xl font-semibold text-white">Статистика</h2>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-gray-300">📋 Всего заданий</span>
                  <span className="text-2xl font-bold text-white">{assignments.length}</span>
                </div>
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <span className="text-gray-300">📝 Всего решений</span>
                  <span className="text-2xl font-bold text-white">{submissions.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">⏳ Ожидают проверки</span>
                  <span className="text-2xl font-bold text-warning">{submissions.filter(s => s.status === 'pending').length}</span>
                </div>
              </div>
            </div>
            
            {/* Последние решения */}
            <div className="gradient-border p-6">
              <div className="flex items-center gap-3 mb-4">
                <FiCheckCircle size={24} className="text-accent" />
                <h2 className="text-xl font-semibold text-white">Последние решения</h2>
              </div>
              {submissions.length === 0 ? (
                <div className="text-center py-8 text-gray-400">Нет решений</div>
              ) : (
                <ul className="space-y-2 max-h-80 overflow-y-auto">
                  {submissions.slice(0, 5).map(sub => (
                    <li key={sub.id} className="border-b border-white/10 pb-2 flex justify-between items-center">
                      <span className="text-gray-300">Задание #{sub.assignment_id}</span>
                      <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${
                        sub.status === 'approved' ? 'status-approved' :
                        sub.status === 'rejected' ? 'status-rejected' : 'status-pending'
                      }`}>
                        {sub.status === 'approved' ? '✅ Зачтено' :
                         sub.status === 'rejected' ? '❌ На доработку' : '⏳ Ожидает'}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ) : (
          // ========== ВИД ДЛЯ УЧЕНИКА ==========
          <>
            {/* Статистика ученика */}
            <div className="grid md:grid-cols-4 gap-4 mb-8">
              <div className="gradient-border p-4 text-center">
                <FiBookOpen size={28} className="text-accent mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{stats.total}</div>
                <div className="text-sm text-gray-400">Всего заданий</div>
              </div>
              <div className="gradient-border p-4 text-center">
                <FiClock size={28} className="text-warning mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{stats.pending}</div>
                <div className="text-sm text-gray-400">Ожидают проверки</div>
              </div>
              <div className="gradient-border p-4 text-center">
                <FiCheckCircle size={28} className="text-success mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{stats.approved}</div>
                <div className="text-sm text-gray-400">Зачтено</div>
              </div>
              <div className="gradient-border p-4 text-center">
                <FiAward size={28} className="text-danger mx-auto mb-2" />
                <div className="text-2xl font-bold text-white">{stats.rejected}</div>
                <div className="text-sm text-gray-400">На доработку</div>
              </div>
            </div>

            {/* Список заданий */}
            <div className="gradient-border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <FiBookOpen size={24} className="text-accent" />
                  <h2 className="text-xl font-semibold text-white">Мои задания</h2>
                </div>
                <Link to="/chats" className="text-accent hover:opacity-80 transition flex items-center gap-1 text-sm">
                  <FiMessageCircle size={16} />
                  <span>Чаты</span>
                </Link>
              </div>
              
              {assignments.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <div className="text-6xl mb-4">📭</div>
                  <p className="text-lg">У вас пока нет заданий</p>
                  <p className="text-sm">Когда учитель добавит задания, они появятся здесь</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {assignments.map(assignment => {
                    const submission = submissions.find(s => s.assignment_id === assignment.id);
                    const isOverdue = new Date(assignment.due_date) < new Date();
                    const isSubmitted = !!submission;
                    const isApproved = submission?.status === 'approved';
                    
                    return (
                      <div 
                        key={assignment.id} 
                        className={`rounded-xl p-4 transition-all duration-200 hover:transform hover:scale-[1.02] ${
                          isOverdue && !isSubmitted 
                            ? 'bg-red-950/20 border border-red-800' 
                            : isApproved
                            ? 'bg-green-950/20 border border-green-800'
                            : 'bg-dark-card border border-white/10'
                        }`}
                      >
                        <div className="flex justify-between items-start flex-wrap gap-2">
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg text-white">{assignment.title}</h3>
                            <p className="text-gray-400 mt-1 line-clamp-2">{assignment.description}</p>
                            <div className="flex items-center gap-3 mt-2 flex-wrap">
                              <span className="text-sm text-gray-500">
                                📅 Дедлайн: {new Date(assignment.due_date).toLocaleDateString()}
                              </span>
                              {isOverdue && !isSubmitted && (
                                <span className="text-xs bg-red-900/50 text-red-400 px-2 py-0.5 rounded-full">⏰ Просрочено</span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {submission ? (
                          <div className="mt-3 pt-3 border-t border-white/10">
                            <div className="flex items-center justify-between flex-wrap gap-2">
                              <span className={`text-sm px-3 py-1 rounded-full ${
                                submission.status === 'approved' ? 'status-approved' :
                                submission.status === 'rejected' ? 'status-rejected' : 'status-pending'
                              }`}>
                                {submission.status === 'approved' ? '✅ Зачтено' :
                                 submission.status === 'rejected' ? '❌ На доработку' : '⏳ Ожидает проверки'}
                              </span>
                              {submission.status !== 'approved' && (
                                <Link to={`/assignment/${assignment.id}`}>
                                  <button className="text-sm text-gray-400 hover:text-accent transition px-3 py-1 rounded-lg bg-white/5">
                                    ✏️ {submission.status === 'rejected' ? 'Исправить' : 'Редактировать'}
                                  </button>
                                </Link>
                              )}
                            </div>
                            {submission.feedback && (
                              <div className="mt-2 text-sm bg-accent-light p-3 rounded-lg">
                                <span className="font-medium text-accent">💬 Фидбек:</span>
                                <p className="text-gray-300 mt-1">{submission.feedback}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <Link to={`/assignment/${assignment.id}`}>
                            <button className="mt-3 btn-primary text-sm">
                              📝 Отправить решение
                            </button>
                          </Link>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AnimatedPage>
  );
};

export default Dashboard;