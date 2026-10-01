import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiDollarSign, FiPlus, FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import toast from 'react-hot-toast';

interface StudentBalance {
  student_id: number;
  student_name: string;
  balance: number;
  total_paid: number;
  total_debt: number;
}

const FinancePage: React.FC = () => {
  const { isTeacher } = useAuth();
  const [students, setStudents] = useState<StudentBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  useEffect(() => {
    if (!isTeacher) return;
    fetchStudents();
  }, [isTeacher]);

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/payments/students');
      const data = Array.isArray(response.data) ? response.data : [];
      setStudents(data);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const addPayment = async () => {
    if (!selectedStudent || !amount) return;
    try {
      await apiClient.post('/payments', {
        student_id: selectedStudent,
        amount: parseFloat(amount),
        note: note || null,
      });
      toast.success('Платёж добавлен');
      setShowModal(false);
      setAmount('');
      setNote('');
      fetchStudents();
    } catch (error) {
      toast.error('Ошибка при добавлении платежа');
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

  const totalIncome = students.reduce((sum, s) => sum + Number(s.total_paid), 0);
  const totalDebt = students.reduce((sum, s) => sum + Number(s.total_debt), 0);

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Финансы</h1>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
          >
            <FiPlus size={18} />
            <span>Добавить платёж</span>
          </button>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="bg-dark-card rounded-xl p-5 border border-white/10">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-green-500/20">
                <FiTrendingUp size={24} className="text-green-400" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">Общий доход</p>
                <p className="text-2xl font-bold text-white">
                  {totalIncome.toLocaleString()} ₽
                </p>
              </div>
            </div>
          </div>
          <div className="bg-dark-card rounded-xl p-5 border border-white/10">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg bg-red-500/20">
                <FiTrendingDown size={24} className="text-red-400" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">Общая задолженность</p>
                <p className="text-2xl font-bold text-white">
                  {totalDebt.toLocaleString()} ₽
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold text-white">Баланс учеников</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Ученик</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Всего оплачено</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Баланс</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-400">Статус</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-400">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {students.map((student) => (
                  <tr key={student.student_id} className="hover:bg-white/5 transition">
                    <td className="px-4 py-3 text-white">{student.student_name}</td>
                    <td className="px-4 py-3 text-right text-white">
                      {Number(student.total_paid).toLocaleString()} ₽
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-semibold ${
                        Number(student.balance) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {Number(student.balance) >= 0 ? '+' : ''}
                      {Number(student.balance).toLocaleString()} ₽
                    </td>
                    <td className="px-4 py-3 text-center">
                      {Number(student.balance) < 0 ? (
                        <span className="inline-block px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">
                          Долг {Math.abs(Number(student.balance))} ₽
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">
                          Переплата {Number(student.balance)} ₽
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => {
                          setSelectedStudent(student.student_id);
                          setShowModal(true);
                        }}
                        className="text-accent hover:text-accent/80 text-sm"
                      >
                        Внести оплату
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Добавить платёж</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Ученик</label>
                  <select
                    value={selectedStudent || ''}
                    onChange={(e) => setSelectedStudent(parseInt(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  >
                    <option value="">Выберите ученика</option>
                    {students.map((s) => (
                      <option key={s.student_id} value={s.student_id}>
                        {s.student_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Сумма (₽)</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="1000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Комментарий (необязательно)
                  </label>
                  <input
                    type="text"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: за март"
                  />
                </div>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={addPayment}
                    disabled={!selectedStudent || !amount}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    Добавить
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

export default FinancePage;