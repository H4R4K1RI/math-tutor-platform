import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import { FiDollarSign, FiCalendar, FiArrowLeft, FiUser } from 'react-icons/fi';
import { Link } from 'react-router-dom';

interface Payment {
  id: number;
  amount: number;
  note: string | null;
  created_at: string;
}

interface TeacherBalance {
  teacher_id: number;
  teacher_name: string;
  balance: number;
  payments: Payment[];
}

const PaymentHistory: React.FC = () => {
  const { user } = useAuth();
  const [balances, setBalances] = useState<TeacherBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTeacher, setExpandedTeacher] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;
    fetchBalances();
  }, [user]);

  const fetchBalances = async () => {
    try {
      const response = await apiClient.get('/payments/my-balances');
      setBalances(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching balances:', error);
      setBalances([]);
    } finally {
      setLoading(false);
    }
  };

  const totalBalance = balances.reduce((sum, b) => sum + Number(b.balance), 0);

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
        <div className="flex items-center gap-4 mb-6">
          <Link to="/dashboard" className="text-gray-400 hover:text-white transition">
            <FiArrowLeft size={24} />
          </Link>
          <h1 className="text-2xl font-bold text-white">Мои платежи</h1>
        </div>

        {/* Общий баланс */}
        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-accent/20">
              <FiDollarSign size={28} className="text-accent" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Общий баланс по всем учителям</p>
              <p
                className={`text-3xl font-bold ${
                  totalBalance >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {totalBalance >= 0 ? '+' : ''}
                {totalBalance.toFixed(2)} ₽
              </p>
              {totalBalance < 0 && (
                <p className="text-sm text-red-400 mt-1">У вас есть задолженность</p>
              )}
            </div>
          </div>
        </div>

        {balances.length === 0 ? (
          <div className="bg-dark-card rounded-xl p-8 border border-white/10 text-center text-gray-400">
            У вас пока нет платежей
          </div>
        ) : (
          <div className="space-y-4">
            {balances.map((b) => (
              <div
                key={b.teacher_id}
                className="bg-dark-card rounded-xl border border-white/10 overflow-hidden"
              >
                <button
                  onClick={() =>
                    setExpandedTeacher(
                      expandedTeacher === b.teacher_id ? null : b.teacher_id
                    )
                  }
                  className="w-full p-4 flex justify-between items-center hover:bg-white/5 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-accent/20">
                      <FiUser size={16} className="text-accent" />
                    </div>
                    <div className="text-left">
                      <p className="text-white font-medium">{b.teacher_name}</p>
                      <p className="text-sm text-gray-400">
                        {b.payments.length} платежей
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-bold ${
                        Number(b.balance) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {Number(b.balance) >= 0 ? '+' : ''}
                      {Number(b.balance).toFixed(2)} ₽
                    </p>
                  </div>
                </button>

                {expandedTeacher === b.teacher_id && (
                  <div className="border-t border-white/10 divide-y divide-white/10">
                    {b.payments.length === 0 ? (
                      <div className="p-4 text-center text-gray-400 text-sm">
                        Нет платежей
                      </div>
                    ) : (
                      b.payments.map((payment) => (
                        <div
                          key={payment.id}
                          className="p-3 flex justify-between items-center"
                        >
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-green-500/20">
                              <FiDollarSign size={14} className="text-green-400" />
                            </div>
                            <div>
                              <p
                                className={`font-medium ${
                                  Number(payment.amount) >= 0
                                    ? 'text-green-400'
                                    : 'text-red-400'
                                }`}
                              >
                                {Number(payment.amount) >= 0 ? '+' : ''}
                                {Number(payment.amount).toFixed(2)} ₽
                              </p>
                              {payment.note && (
                                <p className="text-gray-400 text-sm">{payment.note}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <FiCalendar size={14} />
                            <span>
                              {new Date(payment.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default PaymentHistory;