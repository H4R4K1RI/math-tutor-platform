import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { Submission, Assignment } from '../types';
import toast from 'react-hot-toast';

const ReviewSubmissions: React.FC = () => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [submissionsRes, assignmentsRes] = await Promise.all([
        apiClient.get('/submissions'),
        apiClient.get('/assignments')
      ]);
      console.log('Submissions from server:', submissionsRes.data);
submissionsRes.data.forEach((sub: any) => {
  console.log(`Submission ${sub.id}: files =`, sub.files);
});
      setSubmissions(submissionsRes.data);
      setAssignments(assignmentsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id: number, status: string, feedback: string) => {
    try {
      await apiClient.put(`/submissions/${id}`, { status, feedback });
      fetchData();
    } catch (error) {
      console.error('Error updating submission:', error);
      toast.error('❌ Ошибка при обновлении');
    }
  };

  const getAssignmentTitle = (assignmentId: number) => {
    const assignment = assignments.find(a => a.id === assignmentId);
    return assignment?.title || `Задание #${assignmentId}`;
  };

  if (loading) {
    return <div className="text-center py-10">Загрузка...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Проверка решений</h1>
      
      {submissions.length === 0 ? (
        <p className="text-gray-500">Нет решений</p>
      ) : (
        <div className="space-y-4">
          {submissions.map(sub => (
            <div key={sub.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{getAssignmentTitle(sub.assignment_id)}</h3>
                  <p className="text-gray-600 mt-1">Ученик ID: {sub.student_id}</p>
                  
                  {/* Текст решения */}
                  {sub.content && (
  <div className="mt-3">
    <p className="font-medium text-gray-700">Решение ученика:</p>
    <p className="text-gray-700 bg-gray-50 p-3 rounded mt-1 whitespace-pre-wrap">
      {sub.content}
    </p>
  </div>
)}
                  
                  {/* Файлы */}
                  {sub.files && sub.files !== 'null' && sub.files !== '[]' && (
                    <div className="mt-3">
                      <p className="font-medium text-gray-700">Прикреплённые файлы:</p>
                      <div className="mt-1">
                        {(() => {
                          try {
                            const files = JSON.parse(sub.files);
                            if (!Array.isArray(files) || files.length === 0) return null;
                            return files.map((url: string, idx: number) => (
                              <a 
                                key={idx} 
                                href={`http://localhost:8000${url}`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline block text-sm mt-1"
                              >
                                📎 Скачать файл {idx + 1}
                              </a>
                            ));
                          } catch (e) {
                            console.error('Error parsing files:', e);
                            return <p className="text-sm text-gray-500">Ошибка отображения файлов</p>;
                          }
                        })()}
                      </div>
                    </div>
                  )}
                  
                  {/* Фидбек учителя */}
                  {sub.feedback && (
                    <div className="mt-3">
                      <p className="font-medium text-gray-700">Фидбек:</p>
                      <p className="text-gray-600 bg-blue-50 p-3 rounded mt-1">
                        {sub.feedback}
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="text-right ml-4">
                  <p className={`text-sm font-semibold ${
                    sub.status === 'approved' ? 'text-green-600' :
                    sub.status === 'rejected' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {sub.status === 'approved' ? '✅ Зачтено' :
                     sub.status === 'rejected' ? '❌ На доработку' : '⏳ Ожидает проверки'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(sub.submitted_at).toLocaleString()}
                  </p>
                </div>
              </div>
              
              {sub.status === 'pending' && (
                <div className="mt-4 pt-3 border-t">
                  <textarea
                    id={`feedback-${sub.id}`}
                    placeholder="Введите фидбек для ученика..."
                    className="w-full border rounded p-2 mb-2"
                    rows={3}
                  />
                  <div className="space-x-2">
                    <button
                      onClick={() => {
                        const feedback = (document.getElementById(`feedback-${sub.id}`) as HTMLTextAreaElement).value;
                        updateStatus(sub.id, 'approved', feedback);
                      }}
                      className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                    >
                      ✅ Зачесть
                    </button>
                    <button
                      onClick={() => {
                        const feedback = (document.getElementById(`feedback-${sub.id}`) as HTMLTextAreaElement).value;
                        updateStatus(sub.id, 'rejected', feedback);
                      }}
                      className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                    >
                      ❌ На доработку
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewSubmissions;