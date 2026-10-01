import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import {
  FiCalendar,
  FiClock,
  FiSend,
  FiCheckCircle,
  FiXCircle,
  FiLoader,
  FiX,
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import { socket } from '../socket';

interface LessonRequest {
  id: number;
  teacher_id: number;
  student_id: number;
  student_name?: string;
  title: string | null;
  start_time: string;
  end_time: string;
  status: 'pending' | 'approved' | 'rejected';
  notes: string | null;
  created_at: string;
}

interface Teacher {
  id: number;
  full_name: string;
}

const LessonRequestsPage: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [requests, setRequests] = useState<LessonRequest[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<LessonRequest | null>(null);
  const [approvePrice, setApprovePrice] = useState('');
  const [formData, setFormData] = useState({
    teacher_id: '',
    title: '',
    start_time: '',
    end_time: '',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchRequests();
    if (!isTeacher) fetchTeachers();
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handleNewRequest = () => {
      fetchRequests();
      toast.success('📅 Поступила новая заявка на урок!');
    };

    const handleRequestApproved = () => {
      fetchRequests();
      toast.success('✅ Заявка подтверждена! Урок добавлен в расписание.');
    };

    socket.on('new_lesson_request', handleNewRequest);
    socket.on('lesson_request_approved', handleRequestApproved);

    return () => {
      if (socket) {
        socket.off('new_lesson_request', handleNewRequest);
        socket.off('lesson_request_approved', handleRequestApproved);
      }
    };
  }, []);

  const fetchRequests = async () => {
    try {
      const response = await apiClient.get('/lesson-requests');
      setRequests(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching requests:', error);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await apiClient.get('/users/teachers');
      setTeachers(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching teachers:', error);
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.teacher_id || !formData.start_time || !formData.end_time) {
      toast.error('Заполните все обязательные поля');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post('/lesson-requests', {
        teacher_id: parseInt(formData.teacher_id),
        title: formData.title || null,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        notes: formData.notes || null,
      });
      toast.success('Заявка отправлена! Учитель получит уведомление.');
      setShowModal(false);
      setFormData({
        teacher_id: '',
        title: '',
        start_time: '',
        end_time: '',
        notes: '',
      });
      fetchRequests();
    } catch (error: any) {
      console.error('Error creating request:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при отправке заявки');
    } finally {
      setSubmitting(false);
    }
  };

  const openApproveModal = (request: LessonRequest) => {
    setSelectedRequest(request);
    setApprovePrice('');
    setShowApproveModal(true);
  };

  const handleApprove = async () => {
    if (!selectedRequest) return;

    const price = parseFloat(approvePrice) || 0;

    try {
      await apiClient.put(`/lesson-requests/${selectedRequest.id}`, {
        status: 'approved',
        price: price,
      });
      toast.success('Заявка подтверждена');
      setShowApproveModal(false);
      setSelectedRequest(null);
      setApprovePrice('');
      fetchRequests();
    } catch (error: any) {
      console.error('Error approving request:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при подтверждении');
    }
  };

  const handleReject = async (requestId: number) => {
    if (!confirm('Отклонить заявку?')) return;
    try {
      await apiClient.put(`/lesson-requests/${requestId}`, {
        status: 'rejected',
      });
      toast.success('Заявка отклонена');
      fetchRequests();
    } catch (error) {
      console.error('Error rejecting request:', error);
      toast.error('Ошибка при отклонении');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">
            <FiCheckCircle size={12} /> Подтверждено
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">
            <FiXCircle size={12} /> Отклонено
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">
            <FiLoader size={12} /> Ожидает
          </span>
        );
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

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">
            {isTeacher ? 'Заявки на уроки' : 'Мои заявки'}
          </h1>
          {!isTeacher && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
            >
              <FiSend size={18} />
              <span>Записаться на урок</span>
            </button>
          )}
        </div>

        {requests.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiCalendar size={48} className="mx-auto mb-4 opacity-50" />
            <p>Нет заявок</p>
            {!isTeacher && (
              <p className="text-sm mt-1">
                Нажмите "Записаться на урок", чтобы отправить заявку
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {requests.map((req) => (
              <div
                key={req.id}
                className="bg-dark-card rounded-xl p-5 border border-white/10 hover:border-accent transition"
              >
                <div className="flex justify-between items-start flex-wrap gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-white text-lg">
                        {req.student_name}
                      </h3>
                      {getStatusBadge(req.status)}
                    </div>

                    {req.title && (
                      <p className="text-gray-300 text-sm mb-2">📚 {req.title}</p>
                    )}

                    <div className="flex items-center gap-4 text-gray-400 text-sm mb-2">
                      <div className="flex items-center gap-1">
                        <FiCalendar size={14} />
                        <span>{new Date(req.start_time).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FiClock size={14} />
                        <span>
                          {new Date(req.start_time).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}{' '}
                          -{' '}
                          {new Date(req.end_time).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>

                    {req.notes && (
                      <p className="text-gray-500 text-sm mt-2">📝 {req.notes}</p>
                    )}
                  </div>

                  {isTeacher && req.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => openApproveModal(req)}
                        className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white transition flex items-center gap-2 text-sm"
                      >
                        <FiCheckCircle size={14} />
                        Подтвердить
                      </button>
                      <button
                        onClick={() => handleReject(req.id)}
                        className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white transition flex items-center gap-2 text-sm"
                      >
                        <FiXCircle size={14} />
                        Отклонить
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Модальное окно создания заявки */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">Записаться на урок</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleCreateRequest} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Репетитор *
                  </label>
                  <select
                    value={formData.teacher_id}
                    onChange={(e) =>
                      setFormData({ ...formData, teacher_id: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    required
                  >
                    <option value="">Выберите репетитора</option>
                    {teachers.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.full_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Тема урока (необязательно)
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: Квадратные уравнения"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Начало *
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.start_time}
                      onChange={(e) =>
                        setFormData({ ...formData, start_time: e.target.value })
                      }
                      className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Конец *
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.end_time}
                      onChange={(e) =>
                        setFormData({ ...formData, end_time: e.target.value })
                      }
                      className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Комментарий (необязательно)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData({ ...formData, notes: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Что хотите разобрать, какие вопросы..."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    {submitting ? 'Отправка...' : 'Отправить заявку'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Модальное окно подтверждения с ценой */}
        {showApproveModal && selectedRequest && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">Подтверждение урока</h2>
                <button
                  onClick={() => setShowApproveModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <div className="space-y-4">
                <div className="p-3 bg-gray-800 rounded-lg">
                  <p className="text-gray-300 text-sm">
                    <strong>Ученик:</strong> {selectedRequest.student_name}
                  </p>
                  <p className="text-gray-300 text-sm">
                    <strong>Дата:</strong>{' '}
                    {new Date(selectedRequest.start_time).toLocaleString()}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Стоимость урока (₽)
                  </label>
                  <input
                    type="number"
                    step="100"
                    value={approvePrice}
                    onChange={(e) => setApprovePrice(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: 1000"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Оставьте 0 для бесплатного урока
                  </p>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => setShowApproveModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleApprove}
                    className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white transition"
                  >
                    Подтвердить
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

export default LessonRequestsPage;