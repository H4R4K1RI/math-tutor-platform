import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Assignment, Submission } from '../types';
import { Link } from 'react-router-dom';
import Spinner from '../components/Spinner';

const Dashboard: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assignmentsRes, submissionsRes] = await Promise.all([
          apiClient.get('/assignments'),
          apiClient.get('/submissions')
        ]);
        setAssignments(assignmentsRes.data);
        setSubmissions(submissionsRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Добро пожаловать, {user?.full_name}!</h1>
        <p className="text-gray-500 mt-1">Рады вас видеть на платформе</p>
      </div>
      
      {isTeacher ? (
        // Вид для учителя
        <div className="grid md:grid-cols-2 gap-6">
          {/* Статистика */}
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
          
          {/* Последние решения */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">📋 Последние решения</h2>
            {submissions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-5xl mb-3">📭</div>
                <p>Нет решений</p>
              </div>
            ) : (
              <ul className="space-y-2 max-h-80 overflow-y-auto">
                {submissions.slice(0, 5).map(sub => (
                  <li key={sub.id} className="border-b pb-2 flex justify-between items-center">
                    <span>Задание #{sub.assignment_id}</span>
                    <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${
                      sub.status === 'approved' ? 'bg-green-100 text-green-700' :
                      sub.status === 'rejected' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
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
        // Вид для ученика
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            📚 Мои задания
          </h2>
          {assignments.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
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
                    isOverdue && !submission ? 'border-red-200 bg-red-50' : 'border-gray-100'
                  }`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{assignment.title}</h3>
                        <p className="text-gray-600 mt-1">{assignment.description}</p>
                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          <span className="text-sm text-gray-500 flex items-center gap-1">
                            📅 {new Date(assignment.due_date).toLocaleDateString()}
                          </span>
                          {isOverdue && !submission && (
                            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                              ⏰ Просрочено
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {submission ? (
                      <div className="mt-3 pt-3 border-t">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <span className={`text-sm px-2 py-1 rounded-full ${
                            submission.status === 'approved' ? 'bg-green-100 text-green-700' :
                            submission.status === 'rejected' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>
                            {submission.status === 'approved' ? '✅ Зачтено' :
                             submission.status === 'rejected' ? '❌ На доработку' : '⏳ Ожидает проверки'}
                          </span>
                          {submission.status !== 'approved' && (
                            <Link to={`/assignment/${assignment.id}`}>
                              <button className="text-sm bg-orange-500 text-white px-3 py-1 rounded-lg hover:bg-orange-600 transition">
                                ✏️ {submission.status === 'rejected' ? 'Исправить' : 'Редактировать'}
                              </button>
                            </Link>
                          )}
                        </div>
                        
                        {/* Текст решения ученика */}
                        {submission.content && (
                          <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded-lg">
                            <span className="font-medium">📝 Ваш ответ:</span> {submission.content}
                          </div>
                        )}
                        
                        {/* Файлы ученика */}
                        {submission.files && submission.files !== 'null' && submission.files !== '[]' && (
                          <div className="mt-2 text-sm bg-gray-50 p-2 rounded-lg">
                            <span className="font-medium text-gray-600">📎 Ваши файлы:</span>
                            <div className="mt-1">
                              {(() => {
                                try {
                                  const files = JSON.parse(submission.files);
                                  if (!Array.isArray(files) || files.length === 0) return null;
                                  return files.map((url: string, idx: number) => (
                                    <a 
                                      key={idx} 
                                      href={`http://localhost:8000${url}`} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:underline block text-sm mt-1"
                                    >
                                      📂 Скачать файл {idx + 1}
                                    </a>
                                  ));
                                } catch (e) {
                                  return <p className="text-sm text-gray-500">Ошибка отображения файлов</p>;
                                }
                              })()}
                            </div>
                          </div>
                        )}
                        
                        {/* Фидбек учителя */}
                        {submission.feedback && (
                          <div className="mt-2 text-sm bg-blue-50 p-2 rounded-lg">
                            <span className="font-medium text-blue-700">💬 Фидбек учителя:</span> {submission.feedback}
                          </div>
                        )}
                      </div>
                    ) : (
                      <Link to={`/assignment/${assignment.id}`}>
                        <button className="mt-3 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
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
      )}
    </div>
  );
};

export default Dashboard;