import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Assignment, Submission } from '../types';
import { Link } from 'react-router-dom';
import Spinner from '../components/Spinner';
import Pagination from '../components/Pagination';
import { socket } from '../socket';

const Dashboard: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 10;

  // Для учителя — без пагинации
  const fetchData = async () => {
    try {
      const [assignmentsRes, submissionsRes] = await Promise.all([
        apiClient.get('/assignments'),
        apiClient.get('/submissions')
      ]);
      setAssignments(assignmentsRes.data.items || assignmentsRes.data);
      setSubmissions(submissionsRes.data.items || submissionsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Для ученика — с пагинацией
  const fetchAssignmentsWithPagination = async () => {
    try {
      const response = await apiClient.get('/assignments', { params: { skip, limit } });
      setAssignments(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Error fetching assignments:', error);
    }
  };

  // Загрузка решений для ученика
  const fetchSubmissions = async () => {
    try {
      const response = await apiClient.get('/submissions');
      setSubmissions(response.data.items || response.data);
    } catch (error) {
      console.error('Error fetching submissions:', error);
    }
  };

  useEffect(() => {
  const loadData = async () => {
    setLoading(true);
    try {
      if (isTeacher) {
        await fetchData();
      } else {
        await Promise.all([
          fetchAssignmentsWithPagination(),
          fetchSubmissions()
        ]);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  loadData();
}, [skip, isTeacher]);

  // WebSocket обновления (автообновление)
  useEffect(() => {
    const handleUpdate = () => {
      if (isTeacher) {
        fetchData();
      } else {
        fetchAssignmentsWithPagination();
        fetchSubmissions();
      }
    };
    
    socket.on('assignment_updated', handleUpdate);
    socket.on('submission_updated', handleUpdate);
    socket.on('assignment_deleted', handleUpdate);
    
    return () => {
      socket.off('assignment_updated', handleUpdate);
      socket.off('submission_updated', handleUpdate);
      socket.off('assignment_deleted', handleUpdate);
    };
  }, [skip, isTeacher]);

  const handleRefresh = () => {
    if (isTeacher) {
      fetchData();
    } else {
      fetchAssignmentsWithPagination();
      fetchSubmissions();
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Добро пожаловать, {user?.full_name}!</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Рады вас видеть на платформе</p>
        </div>
      </div>
      
      {isTeacher ? (
        // Вид учителя (без пагинации)
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">📊 Статистика</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center border-b border-blue-400 pb-2">
                <span>📋 Всего заданий</span>
                <span className="text-2xl font-bold">{assignments.length}</span>
              </div>
              <div className="flex justify-between items-center border-b border-blue-400 pb-2">
                <span>📝 Всего решений</span>
                <span className="text-2xl font-bold">{submissions.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>⏳ Ожидают проверки</span>
                <span className="text-2xl font-bold">{submissions.filter(s => s.status === 'pending').length}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-[#1a1a1a] rounded-xl shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 dark:text-white">📋 Последние решения</h2>
            {submissions.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <div className="text-5xl mb-3">📭</div>
                <p>Нет решений</p>
              </div>
            ) : (
              <ul className="space-y-2 max-h-80 overflow-y-auto">
                {submissions.slice(0, 5).map(sub => (
                  <li key={sub.id} className="border-b dark:border-gray-700 pb-2 flex justify-between items-center">
                    <span className="dark:text-gray-300">Задание #{sub.assignment_id}</span>
                    <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${
                      sub.status === 'approved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      sub.status === 'rejected' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
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
        // Вид ученика (с пагинацией)
        <div className="bg-white dark:bg-[#1a1a1a] rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 dark:text-white">📚 Мои задания</h2>
          {assignments.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-lg">У вас пока нет заданий</p>
              <p className="text-sm">Когда учитель добавит задания, они появятся здесь</p>
            </div>
          ) : (
            <div className="space-y-4">
              {assignments.map(assignment => {
                const submission = submissions.find(s => s.assignment_id === assignment.id);
                const isOverdue = new Date(assignment.due_date) < new Date();
                return (
                  <div key={assignment.id} className={`border rounded-xl p-4 transition-all hover:shadow-md ${
                    isOverdue && !submission ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20' : 'border-gray-200 dark:border-gray-700'
                  }`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg dark:text-white">{assignment.title}</h3>
                        <p className="text-gray-600 dark:text-gray-400 mt-1">{assignment.description}</p>
                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          <span className="text-sm text-gray-500 dark:text-gray-500 flex items-center gap-1">
                            📅 {new Date(assignment.due_date).toLocaleDateString()}
                          </span>
                          {isOverdue && !submission && (
                            <span className="text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                              ⏰ Просрочено
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {submission ? (
                      <div className="mt-3 pt-3 border-t dark:border-gray-700">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <span className={`text-sm px-2 py-1 rounded-full ${
                            submission.status === 'approved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            submission.status === 'rejected' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                          }`}>
                            {submission.status === 'approved' ? '✅ Зачтено' :
                             submission.status === 'rejected' ? '❌ На доработку' : '⏳ Ожидает проверки'}
                          </span>
                          {submission.status !== 'approved' && (
                            <Link to={`/assignment/${assignment.id}`}>
                              <button className="text-sm text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] dark:hover:text-[#4a9b6e] transition">
                                ✏️ {submission.status === 'rejected' ? 'Исправить' : 'Редактировать'}
                              </button>
                            </Link>
                          )}
                        </div>
                        
                        {submission.content && (
                          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-[#2a2a2a] p-2 rounded-lg">
                            <span className="font-medium">📝 Ваш ответ:</span> {submission.content}
                          </div>
                        )}
                        
                        {submission.feedback && (
                          <div className="mt-2 text-sm bg-blue-50 dark:bg-[#1a2a1a] p-2 rounded-lg">
                            <span className="font-medium text-blue-700 dark:text-blue-400">💬 Фидбек учителя:</span> {submission.feedback}
                          </div>
                        )}
                      </div>
                    ) : (
                      <Link to={`/assignment/${assignment.id}`}>
                        <button className="mt-3 bg-[#2e7d5e] hover:bg-[#1e5a44] text-white px-4 py-2 rounded-lg transition flex items-center gap-2">
                          📝 Отправить решение
                        </button>
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          
          <Pagination
            total={total}
            limit={limit}
            skip={skip}
            onPageChange={(newSkip) => setSkip(newSkip)}
          />
        </div>
      )}
    </div>
  );
};

export default Dashboard;
