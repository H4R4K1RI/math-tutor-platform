import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiArrowLeft, FiUser, FiMail, FiTrash2 } from 'react-icons/fi';

interface Student {
  id: number;
  name: string;
  email: string;
}

interface Group {
  id: number;
  name: string;
  description: string | null;
}

const GroupDetailPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isTeacher } = useAuth();
  const [group, setGroup] = useState<Group | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isTeacher) return;
    fetchGroup();
    fetchStudents();
  }, [id, isTeacher]);

  const fetchGroup = async () => {
    try {
      const response = await apiClient.get('/groups');
      const found = response.data.find((g: any) => g.id === Number(id));
      setGroup(found);
    } catch (error) {
      console.error('Error fetching group:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get(`/groups/${id}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    } finally {
      setLoading(false);
    }
  };

  const removeStudent = async (studentId: number) => {
    if (!confirm('Удалить ученика из группы?')) return;
    try {
      await apiClient.delete(`/groups/${id}/students/${studentId}`);
      fetchStudents();
      // Обновляем список групп на главной странице (обновим при возврате)
    } catch (error) {
      console.error('Error removing student:', error);
      alert('Ошибка при удалении ученика');
    }
  };

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка...</p>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <button
          onClick={() => navigate('/groups')}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition mb-6"
        >
          <FiArrowLeft size={20} />
          <span>Назад к группам</span>
        </button>

        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <h1 className="text-2xl font-bold text-white">{group?.name}</h1>
          {group?.description && (
            <p className="text-gray-400 mt-2">{group.description}</p>
          )}
          <p className="text-gray-500 text-sm mt-4">{students.length} учеников</p>
        </div>

        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold text-white">Ученики в группе</h2>
          </div>
          <div className="divide-y divide-white/10">
            {students.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                В этой группе пока нет учеников
              </div>
            ) : (
              students.map((student) => (
                <div key={student.id} className="p-4 flex justify-between items-center hover:bg-white/5 transition">
                  <div>
                    <div className="flex items-center gap-2">
                      <FiUser size={16} className="text-accent" />
                      <span className="text-white font-medium">{student.name}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-gray-400 text-sm">
                      <FiMail size={12} />
                      <span>{student.email}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => removeStudent(student.id)}
                    className="text-gray-400 hover:text-red-400 transition p-2"
                    title="Удалить из группы"
                  >
                    <FiTrash2 size={18} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default GroupDetailPage;