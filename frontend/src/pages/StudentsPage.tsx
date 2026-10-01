import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiUser, FiMail, FiTrendingUp, FiCheckCircle, FiUsers } from 'react-icons/fi';
import Pagination from '../components/Pagination';

interface Student {
  id: number;
  name: string;
  email: string;
  total_assignments: number;
  completed: number;
  progress: number;
  last_active: string | null;
}

const StudentsPage: React.FC = () => {
  const { isTeacher } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 10;

  useEffect(() => {
    if (!isTeacher) return;
    fetchStudents();
  }, [isTeacher, skip]);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/students', { params: { skip, limit } });
      setStudents(response.data.items || response.data);
      setTotal(response.data.total || response.data.length);
    } catch (error) {
      console.error('Error fetching students:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateInvite = async () => {
    try {
      const response = await apiClient.post('/invitations/generate');
      const fullUrl = `${window.location.origin}${response.data.url}`;
      setInviteLink(fullUrl);
    } catch (error) {
      console.error('Error generating invite:', error);
      alert('Ошибка при создании приглашения');
    }
  };

  const copyToClipboard = () => {
    if (inviteLink) {
      navigator.clipboard.writeText(inviteLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isTeacher) return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  if (loading && students.length === 0) return <div className="text-center py-20 text-white"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div><p>Загрузка учеников...</p></div>;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Мои ученики</h1>
          <button onClick={generateInvite} className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2">
            <FiUsers size={18} /><span>Пригласить ученика</span>
          </button>
        </div>
        {students.length === 0 ? (
          <div className="text-center py-20 text-gray-400"><FiUser size={48} className="mx-auto mb-4 opacity-50" /><p>У вас пока нет учеников</p><p className="text-sm">Нажмите "Пригласить ученика", чтобы добавить первого ученика</p></div>
        ) : (
          <>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {students.map((student) => (
                <Link key={student.id} to={`/students/${student.id}`} className="block bg-dark-card rounded-xl p-5 border border-white/10 hover:shadow-lg hover:border-accent transition-all duration-200">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2"><FiUser className="text-accent" size={18} /><h3 className="font-semibold text-white text-lg truncate">{student.name}</h3></div>
                      <div className="flex items-center gap-2 text-gray-400 text-sm mb-3"><FiMail size={14} /><span className="truncate">{student.email}</span></div>
                      <div className="mt-3">
                        <div className="flex justify-between text-sm text-gray-400 mb-1"><span>Прогресс</span><span>{student.progress}%</span></div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden"><div className="bg-accent h-2 rounded-full transition-all duration-500" style={{ width: `${Math.min(student.progress, 100)}%` }} /></div>
                      </div>
                      <div className="flex gap-4 mt-4 text-sm">
                        <div className="flex items-center gap-1 text-gray-400"><FiTrendingUp size={14} /><span>{student.total_assignments} заданий</span></div>
                        <div className="flex items-center gap-1 text-green-400"><FiCheckCircle size={14} /><span>{student.completed} выполнено</span></div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <Pagination total={total} limit={limit} skip={skip} onPageChange={(newSkip) => setSkip(newSkip)} />
          </>
        )}
        {inviteLink && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Приглашение ученика</h2>
              <p className="text-gray-400 mb-2">Отправьте эту ссылку ученику:</p>
              <div className="flex gap-2 mb-4">
                <input type="text" value={inviteLink} readOnly className="flex-1 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm" />
                <button onClick={copyToClipboard} className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition">{copied ? '✅' : '📋'}</button>
              </div>
              <p className="text-sm text-gray-500">Ссылка действительна 7 дней</p>
              <p className="text-sm text-yellow-500 mt-1">📌 При регистрации ученик должен выбрать роль "Ученик"</p>
              <button onClick={() => setInviteLink(null)} className="mt-4 w-full px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition">Закрыть</button>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default StudentsPage;