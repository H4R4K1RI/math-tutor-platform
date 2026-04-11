import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { Assignment, Submission } from '../types';
import toast from 'react-hot-toast';
const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';
const AssignmentDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [content, setContent] = useState('');
  const [fileUrl, setFileUrl] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [assignmentRes, submissionsRes] = await Promise.all([
        apiClient.get(`/assignments/${id}`),
        apiClient.get('/submissions')
      ]);
      setAssignment(assignmentRes.data);
      const existing = submissionsRes.data.find((s: Submission) => s.assignment_id === Number(id));
      if (existing) {
        setSubmission(existing);
        setContent(existing.content || '');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    const submitData = {
      assignment_id: Number(id),
      content: content,
      files: fileUrl ? `["${fileUrl}"]` : (submission?.files || null)
    };
    
    console.log('Sending submission:', submitData);
    
    if (submission) {
      // Обновляем существующее решение
      await apiClient.put(`/submissions/${submission.id}`, submitData);
      toast.success('✅ Решение обновлено!');
    } else {
      // Создаём новое решение
      await apiClient.post('/submissions', submitData);
      toast.success('✅ Решение отправлено!');
    }
    navigate('/dashboard');
  } catch (error) {
    console.error('Error submitting solution:', error);
    toast.error('❌ Ошибка при отправке');
  }
};

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    setFileUrl(response.data.url);
    toast.success('✅ Файл загружен!');
  };

  if (loading) return <div className="text-center py-10">Загрузка...</div>;
  if (!assignment) return <div className="text-center py-10">Задание не найдено</div>;

  return (
    <div className="container mx-auto p-4 max-w-3xl">
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h1 className="text-2xl font-bold mb-4">{assignment.title}</h1>
        <p className="text-gray-700 whitespace-pre-wrap">{assignment.description}</p>
        {assignment.attachments && (
          <div className="mt-4">
            <h3 className="font-semibold">Вложения:</h3>
            {JSON.parse(assignment.attachments).map((url: string, idx: number) => (
              <a key={idx} href={`${SERVER_URL}${url}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 block hover:underline">
                Скачать файл {idx + 1}
              </a>
            ))}
          </div>
        )}
        <p className="text-sm text-gray-500 mt-4">Дедлайн: {new Date(assignment.due_date).toLocaleString()}</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Отправить решение</h2>
        {submission && submission.status !== 'pending' && (
          <div className={`p-3 rounded mb-4 ${submission.status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            <p className="font-semibold">{submission.status === 'approved' ? '✅ Зачтено!' : '❌ На доработку'}</p>
            {submission.feedback && <p className="mt-1">{submission.feedback}</p>}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Введите решение..."
            className="w-full border rounded p-2"
            rows={6}
          />
          <div>
            <label className="block text-sm font-medium mb-1">Прикрепить файл</label>
            <input type="file" onChange={handleFileUpload} className="border rounded p-1" />
            {fileUrl && <p className="text-green-600 text-sm mt-1">✅ Файл загружен</p>}
          </div>
          <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
            {submission ? 'Обновить решение' : 'Отправить решение'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AssignmentDetail;