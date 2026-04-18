import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { Assignment, Submission } from '../types';
import toast from 'react-hot-toast';
import { FiMessageCircle } from 'react-icons/fi';

const AssignmentDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [content, setContent] = useState('');
  const [fileUrls, setFileUrls] = useState<string[]>([]);
  const [existingFileUrls, setExistingFileUrls] = useState<string[]>([]);
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
      const submissionsData = submissionsRes.data.items || submissionsRes.data;
const existing = submissionsData.find((s: Submission) => s.assignment_id === Number(id));
      if (existing) {
        setSubmission(existing);
        setContent(existing.content || '');
        if (existing.files) {
          try {
            const files = JSON.parse(existing.files);
            if (Array.isArray(files)) {
              setExistingFileUrls(files);
            }
          } catch (e) {}
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMultipleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    const newUrls: string[] = [];
    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      newUrls.push(response.data.url);
    }
    setFileUrls([...fileUrls, ...newUrls]);
    toast.success(`Загружено файлов: ${newUrls.length}`);
  };

  const removeFile = (index: number) => {
    setFileUrls(fileUrls.filter((_, i) => i !== index));
  };

  const removeExistingFile = (index: number) => {
    setExistingFileUrls(existingFileUrls.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const allFiles = [...existingFileUrls, ...fileUrls];
      const filesValue = allFiles.length > 0 ? JSON.stringify(allFiles) : null;
      
      const submitData = {
        assignment_id: Number(id),
        content: content || null,
        files: filesValue
      };
      
      if (submission) {
        await apiClient.put(`/submissions/${submission.id}`, submitData);
        toast.success('✅ Решение обновлено!');
      } else {
        await apiClient.post('/submissions', submitData);
        toast.success('✅ Решение отправлено!');
      }
      navigate('/dashboard');
    } catch (error) {
      console.error('Error submitting solution:', error);
      toast.error('❌ Ошибка при отправке');
    }
  };

  const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';

  if (loading) return <div className="text-center py-10">Загрузка...</div>;
  if (!assignment) return <div className="text-center py-10">Задание не найдено</div>;

  return (
    <div className="container mx-auto p-4 max-w-3xl">
      <div className="bg-white dark:bg-[#1a1a1a] rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-start">
          <h1 className="text-2xl font-bold mb-4 dark:text-white">{assignment.title}</h1>
          <button
            onClick={() => navigate(`/chat/assignment/${assignment.id}`)}
            className="text-[#2e7d5e] hover:text-[#1e5a44] transition"
            title="Обсудить задание"
          >
            <FiMessageCircle size={24} />
          </button>
        </div>
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{assignment.description}</p>
        {assignment.attachments && (
          <div className="mt-4">
            <h3 className="font-semibold dark:text-white">Материалы к заданию:</h3>
            {JSON.parse(assignment.attachments).map((url: string, idx: number) => (
              <a key={idx} href={`${SERVER_URL}${url}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-[#4a9b6e] block hover:underline">
                📎 Скачать файл {idx + 1}
              </a>
            ))}
          </div>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">Дедлайн: {new Date(assignment.due_date).toLocaleString()}</p>
      </div>

      <div className="bg-white dark:bg-[#1a1a1a] rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">Отправить решение</h2>
        {submission && submission.status !== 'pending' && (
          <div className={`p-3 rounded mb-4 ${submission.status === 'approved' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'}`}>
            <p className="font-semibold">{submission.status === 'approved' ? '✅ Зачтено!' : '❌ На доработку'}</p>
            {submission.feedback && <p className="mt-1">{submission.feedback}</p>}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Введите решение..."
            className="w-full border rounded-lg p-2 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
            rows={6}
          />
          <div>
            <label className="block text-sm font-medium mb-1 dark:text-gray-300">Прикрепить файлы (можно несколько)</label>
            <input type="file" multiple onChange={handleMultipleFileUpload} className="border rounded-lg p-1 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white" />
            
            {existingFileUrls.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-600 dark:text-gray-400">Текущие файлы:</p>
                {existingFileUrls.map((url, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-50 dark:bg-[#2a2a2a] p-2 rounded mt-1">
                    <a href={`${SERVER_URL}${url}`} target="_blank" className="text-[#2e7d5e] dark:text-[#4a9b6e] text-sm">
                      📎 Файл {idx + 1}
                    </a>
                    <button type="button" onClick={() => removeExistingFile(idx)} className="text-red-500 text-sm">
                      ✖ Удалить
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {fileUrls.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-600 dark:text-gray-400">Новые файлы:</p>
                {fileUrls.map((url, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-50 dark:bg-[#2a2a2a] p-2 rounded mt-1">
                    <a href={`${SERVER_URL}${url}`} target="_blank" className="text-[#2e7d5e] dark:text-[#4a9b6e] text-sm">
                      📎 Новый файл {idx + 1}
                    </a>
                    <button type="button" onClick={() => removeFile(idx)} className="text-red-500 text-sm">
                      ✖ Удалить
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button type="submit" className="bg-[#2e7d5e] hover:bg-[#1e5a44] text-white px-6 py-2 rounded-lg transition">
            {submission ? 'Обновить решение' : 'Отправить решение'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AssignmentDetail;
