import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import {
  FiStar,
  FiUsers,
  FiCalendar,
  FiMessageCircle,
  FiSend,
  FiShare2,
  FiX,
} from 'react-icons/fi';
import toast from 'react-hot-toast';

interface Review {
  id: number;
  student_id: number;
  student_name: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

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
}

const TutorPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isTeacher } = useAuth();
  const [tutor, setTutor] = useState<TutorProfile | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Статус связи
  const [isConnected, setIsConnected] = useState(false);
  const [chatId, setChatId] = useState<number | null>(null);
  const [hasPendingRequest, setHasPendingRequest] = useState(false);

  // Модалка заявки
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [requestMessage, setRequestMessage] = useState('');
  const [sendingRequest, setSendingRequest] = useState(false);

  useEffect(() => {
    fetchTutor();
    fetchReviews();
    if (user && !isTeacher) {
      checkConnection();
    }
  }, [id, user]);

  const fetchTutor = async () => {
    try {
      const response = await apiClient.get(`/users/tutor/${id}`);
      setTutor(response.data);
    } catch (error) {
      console.error('Error fetching tutor:', error);
    }
  };

  const fetchReviews = async () => {
    try {
      const response = await apiClient.get(`/reviews/tutor/${id}`);
      setReviews(Array.isArray(response.data) ? response.data : []);
    } finally {
      setLoading(false);
    }
  };

  const checkConnection = async () => {
    try {
      const response = await apiClient.get(`/tutoring-requests/check/${id}`);
      setIsConnected(response.data.is_connected);
      setChatId(response.data.chat_id);
      setHasPendingRequest(response.data.has_pending_request);
    } catch (error) {
      console.error('Error checking connection:', error);
    }
  };

  const sendTutoringRequest = async () => {
    setSendingRequest(true);
    try {
      await apiClient.post('/tutoring-requests/', {
        teacher_id: parseInt(id || '0'),
        message: requestMessage || null,
      });
      toast.success('Заявка отправлена! Учитель получит уведомление.');
      setShowRequestModal(false);
      setRequestMessage('');
      setHasPendingRequest(true);
    } catch (error: any) {
      console.error('Error sending request:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при отправке заявки');
    } finally {
      setSendingRequest(false);
    }
  };

  const handleSubmitReview = async () => {
    if (!user) {
      toast.error('Войдите в аккаунт, чтобы оставить отзыв');
      navigate('/login');
      return;
    }

    if (isTeacher) {
      toast.error('Только ученики могут оставлять отзывы');
      return;
    }

    if (reviewRating < 1 || reviewRating > 5) {
      toast.error('Выберите оценку от 1 до 5');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post(`/reviews/tutor/${id}`, {
        rating: reviewRating,
        comment: reviewComment || null,
        lesson_id: null,
      });
      toast.success('Отзыв оставлен!');
      setShowReviewModal(false);
      setReviewRating(5);
      setReviewComment('');
      fetchReviews();
      fetchTutor();
    } catch (error: any) {
      console.error('Error submitting review:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при отправке отзыва');
    } finally {
      setSubmitting(false);
    }
  };

  const copyProfileLink = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success('Ссылка на профиль скопирована');
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    for (let i = 1; i <= 5; i++) {
      if (i <= fullStars) {
        stars.push(<FiStar key={i} className="fill-yellow-400 text-yellow-400" size={16} />);
      } else {
        stars.push(<FiStar key={i} className="text-gray-500" size={16} />);
      }
    }
    return stars;
  };

  const getInitials = (name: string) => name.charAt(0).toUpperCase();

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

  const avatarUrl = tutor.avatar?.startsWith('/static') ? tutor.avatar : tutor.avatar;

  // Логика динамической кнопки
  const renderActionButton = () => {
    if (!user) {
      return (
        <button
          onClick={() => navigate('/login')}
          className="w-full md:w-auto px-6 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition"
        >
          Войти, чтобы присоединиться
        </button>
      );
    }

    if (user.id === tutor.id) {
      return (
        <button
          onClick={() => navigate('/profile')}
          className="w-full md:w-auto px-6 py-3 rounded-lg bg-gray-700 hover:bg-gray-600 text-white font-medium transition"
        >
          Редактировать профиль
        </button>
      );
    }

    if (isTeacher) {
      return null;
    }

    if (isConnected && chatId) {
      return (
        <button
          onClick={() => navigate(`/chat/${chatId}`)}
          className="w-full md:w-auto px-6 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition flex items-center justify-center gap-2"
        >
          <FiMessageCircle size={18} />
          Написать репетитору
        </button>
      );
    }

    if (hasPendingRequest) {
      return (
        <button
          disabled
          className="w-full md:w-auto px-6 py-3 rounded-lg bg-gray-700 text-gray-400 font-medium cursor-not-allowed"
        >
          Заявка отправлена
        </button>
      );
    }

    return (
      <button
        onClick={() => setShowRequestModal(true)}
        className="w-full md:w-auto px-6 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium transition flex items-center justify-center gap-2"
      >
        <FiSend size={18} />
        Присоединиться
      </button>
    );
  };

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          {/* Шапка профиля */}
          <div className="p-6 border-b border-white/10">
            <div className="flex justify-end mb-2">
              <button
                onClick={copyProfileLink}
                className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition text-sm flex items-center gap-2"
              >
                <FiShare2 size={14} />
                Поделиться
              </button>
            </div>
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-shrink-0">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt={tutor.full_name}
                    className="w-32 h-32 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-accent/20 flex items-center justify-center">
                    <span className="text-4xl text-accent font-bold">
                      {getInitials(tutor.full_name)}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-white">{tutor.full_name}</h1>
                <div className="flex items-center gap-2 mt-2">
                  <div className="flex items-center gap-1">{renderStars(tutor.rating)}</div>
                  <span className="text-white">{tutor.rating.toFixed(1)}</span>
                  <span className="text-gray-400">
                    · {reviews.length} {reviews.length === 1 ? 'отзыв' : reviews.length < 5 ? 'отзыва' : 'отзывов'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-4 mt-4 text-gray-400">
                  <div className="flex items-center gap-2">
                    <FiUsers size={16} />
                    <span>{tutor.total_students} учеников</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FiCalendar size={16} />
                    <span>
                      Опыт: {tutor.experience_years}{' '}
                      {tutor.experience_years === 1 ? 'год' : tutor.experience_years < 5 ? 'года' : 'лет'}
                    </span>
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

          {/* Отзывы */}
          <div className="p-6 border-b border-white/10">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">📖 Отзывы учеников</h2>
              {user && !isTeacher && (
                <button
                  onClick={() => setShowReviewModal(true)}
                  className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2 text-sm"
                >
                  <FiSend size={14} />
                  <span>Оставить отзыв</span>
                </button>
              )}
            </div>

            {reviews.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p>Пока нет отзывов</p>
                {!isTeacher && <p className="text-sm mt-1">Будьте первым, кто оставит отзыв!</p>}
              </div>
            ) : (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <div key={review.id} className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                            <span className="text-accent font-bold text-sm">
                              {getInitials(review.student_name)}
                            </span>
                          </div>
                          <span className="font-medium text-white">{review.student_name}</span>
                        </div>
                        <div className="flex items-center gap-1 mt-1">
                          {renderStars(review.rating)}
                        </div>
                        {review.comment && (
                          <p className="text-gray-300 mt-2">{review.comment}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Динамическая кнопка */}
          <div className="p-6 bg-white/5">{renderActionButton()}</div>
        </div>

        {/* Модалка отзыва */}
        {showReviewModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">Оставить отзыв</h2>
                <button
                  onClick={() => setShowReviewModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ваша оценка
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setReviewRating(star)}
                        className="focus:outline-none"
                      >
                        <FiStar
                          size={32}
                          className={`transition ${
                            star <= reviewRating
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-500 hover:text-yellow-400'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Комментарий (необязательно)
                  </label>
                  <textarea
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Расскажите о своём опыте занятий..."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => setShowReviewModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleSubmitReview}
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    {submitting ? 'Отправка...' : 'Отправить отзыв'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Модалка заявки */}
        {showRequestModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Заявка на обучение
                </h2>
                <button
                  onClick={() => setShowRequestModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <p className="text-gray-400 text-sm mb-4">
                Отправьте заявку репетитору <strong>{tutor.full_name}</strong>. Он
                получит уведомление и сможет принять или отклонить её.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Сообщение (необязательно)
                  </label>
                  <textarea
                    value={requestMessage}
                    onChange={(e) => setRequestMessage(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Хочу заниматься математикой, готовлюсь к ЕГЭ..."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => setShowRequestModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={sendTutoringRequest}
                    disabled={sendingRequest}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    {sendingRequest ? 'Отправка...' : 'Отправить заявку'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default TutorPage;