import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import { FiUser, FiMail, FiBriefcase, FiBookOpen, FiStar, FiUsers, FiCalendar } from 'react-icons/fi';

interface TutorProfile {
  id: number;
  full_name: string;
  avatar: string | null;
  about: string | null;
  education: string | null;
  experience_years: number;
  rating: number;
  total_students: number;
  total_lessons: number;
  subjects: { id: number; name: string }[];
}

const TutorPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tutor, setTutor] = useState<TutorProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTutor();
  }, [id]);

  const fetchTutor = async () => {
    try {
      const response = await apiClient.get(`/users/tutor/${id}`);
      setTutor(response.data);
    } catch (error) {
      console.error('Error fetching tutor:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (!tutor) {
    return <div className="text-center py-20 text-white">Репетитор не найден</div>;
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          {/* Шапка профиля */}
          <div className="p-6 border-b border-white/10">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-shrink-0">
                {tutor.avatar ? (
                  <img src={tutor.avatar} alt={tutor.full_name} className="w-32 h-32 rounded-full object-cover" />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-accent/20 flex items-center justify-center">
                    <span className="text-4xl text-accent font-bold">{tutor.full_name.charAt(0)}</span>
                  </div>
                )}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-white">{tutor.full_name}</h1>
                <div className="flex items-center gap-2 mt-2">
                  <FiStar className="text-yellow-400" />
                  <span className="text-white">{tutor.rating.toFixed(1)}</span>
                  <span className="text-gray-400">· {tutor.total_lessons} уроков</span>
                </div>
                <div className="flex flex-wrap gap-4 mt-4 text-gray-400">
                  <div className="flex items-center gap-2">
                    <FiUsers size={16} />
                    <span>{tutor.total_students} учеников</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FiCalendar size={16} />
                    <span>Опыт: {tutor.experience_years} лет</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* О себе */}
          {tutor.about && (
            <div className="p-6 border-b border-white/10">
              <h2 className="text-xl font-semibold text-white mb-3">📝 О себе</h2>
              <p className="text-gray-300 whitespace-pre-wrap">{tutor.about}</p>
            </div>
          )}

          {/* Образование */}
          {tutor.education && (
            <div className="p-6 border-b border-white/10">
              <h2 className="text-xl font-semibold text-white mb-3">🎓 Образование</h2>
              <p className="text-gray-300 whitespace-pre-wrap">{tutor.education}</p>
            </div>
          )}

          {/* Кнопка действий (если пользователь не репетитор) */}
          <div className="p-6 bg-white/5">
            <button
              onClick={() => navigate(`/chats?tutor=${tutor.id}`)}
              className="w-full md:w-auto px-6 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition"
            >
              Написать репетитору
            </button>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TutorPage;