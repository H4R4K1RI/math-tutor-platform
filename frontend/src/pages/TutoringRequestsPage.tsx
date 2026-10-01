import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import {
  FiCheckCircle,
  FiXCircle,
  FiLoader,
  FiUsers,
  FiMail,
  FiX,
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import { socket } from '../socket';

interface TutoringRequest {
  id: number;
  teacher_id: number;
  student_id: number;
  student_name: string;
  teacher_name: string;
  message: string | null;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

const TutoringRequestsPage: React.FC = () => {
  const { isTeacher } = useAuth();
  const [requests, setRequests] = useState<TutoringRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<number | null>(null);

  useEffect(() => {
    fetchRequests();
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handleNew = () => {
      fetchRequests();
      toast.success('📩 Новая заявка на обучение!');
    };

    const handleApproved = () => {
      fetchRequests();
      toast.success('✅ Заявка принята!');
    };

    socket.on('new_tutoring_request', handleNew);
    socket.on('tutoring_request_approved', handleApproved);

    return () => {
      if (socket) {
        socket.off('new_tutoring_request', handleNew);
        socket.off('tutoring_request_approved', handleApproved);
      }
    };
  }, []);

  const fetchRequests = async () => {
    try {
      const response = await apiClient.get('/tutoring-requests');
      setRequests(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching tutoring requests:', error);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (requestId: number, status: 'approved' | 'rejected') => {
    if (status === 'rejected' && !confirm('Отклонить заявку?')) return;

    setProcessingId(requestId);
    try {
      await apiClient.put(`/tutoring-requests/${requestId}`, { status });
      toast.success(status === 'approved' ? 'Заявка принята' : 'Заявка отклонена');
      fetchRequests();
    } catch (error: any) {
      console.error('Error updating request:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при обработке заявки');
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">
            <FiCheckCircle size={12} /> Принята
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">
            <FiXCircle size={12} /> Отклонена
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
        <p>Загрузка заявок...</p>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">
            {isTeacher ? 'Заявки на обучение' : 'Мои заявки на обучение'}
          </h1>
        </div>

        {requests.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiUsers size={48} className="mx-auto mb-4 opacity-50" />
            <p>Нет заявок</p>
            {!isTeacher && (
              <p className="text-sm mt-1">
                Найдите репетитора и отправьте заявку с его публичной карточки
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
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h3 className="font-semibold text-white text-lg">
                        {isTeacher ? req.student_name : req.teacher_name}
                      </h3>
                      {getStatusBadge(req.status)}
                    </div>

                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                      <FiMail size={14} />
                      <span>
                        {isTeacher
                          ? 'Ученик хочет заниматься с вами'
                          : `Заявка репетитору: ${req.teacher_name}`}
                      </span>
                    </div>

                    {req.message && (
                      <div className="mt-2 p-3 bg-gray-800/50 rounded-lg">
                        <p className="text-gray-300 text-sm whitespace-pre-wrap">
                          💬 {req.message}
                        </p>
                      </div>
                    )}

                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(req.created_at).toLocaleString()}
                    </p>
                  </div>

                  {isTeacher && req.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => updateStatus(req.id, 'approved')}
                        disabled={processingId === req.id}
                        className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white transition flex items-center gap-2 text-sm disabled:opacity-50"
                      >
                        <FiCheckCircle size={14} />
                        Принять
                      </button>
                      <button
                        onClick={() => updateStatus(req.id, 'rejected')}
                        disabled={processingId === req.id}
                        className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white transition flex items-center gap-2 text-sm disabled:opacity-50"
                      >
                        <FiXCircle size={14} />
                        Отклонить
                      </button>
                    </div>
                  )}

                  {!isTeacher && req.status === 'pending' && (
                    <div className="text-sm text-yellow-400">
                      Ожидает решения репетитора
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default TutoringRequestsPage;