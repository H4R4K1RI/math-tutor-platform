import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import { Calendar, dateFnsLocalizer, Views, View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, addMonths, subMonths } from 'date-fns';
import { ru } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import {
  FiPlus,
  FiX,
  FiChevronLeft,
  FiChevronRight,
  FiCalendar as FiCalendarIcon,
  FiClock,
  FiDollarSign,
  FiUser,
  FiEdit2,
  FiVideo,
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const locales = { ru };

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface Lesson {
  id: number;
  title: string;
  student_id: number;
  student_name?: string;
  start_time: string;
  end_time: string;
  price: number;
  status: string;
  notes?: string;
}

interface Student {
  id: number;
  name: string;
  email: string;
}

interface CalendarEvent {
  id: number;
  title: string;
  rawTitle: string;
  start: Date;
  end: Date;
  status: string;
  price: number;
  notes?: string;
  student_name?: string;
  student_id: number;
}

const CalendarPage: React.FC = () => {
  const { isTeacher } = useAuth();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showLessonModal, setShowLessonModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedLesson, setSelectedLesson] = useState<CalendarEvent | null>(null);
  const [currentView, setCurrentView] = useState<View>(Views.MONTH);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  // Форма создания
  const [formData, setFormData] = useState({
    student_id: '',
    title: '',
    start_time: '',
    end_time: '',
    price: '',
    notes: '',
  });

  // Форма редактирования
  const [editData, setEditData] = useState({
    title: '',
    price: '',
    notes: '',
    status: 'scheduled',
  });

  useEffect(() => {
    fetchLessons();
    if (isTeacher) fetchStudents();
  }, []);

  const fetchLessons = async () => {
    try {
      const response = await apiClient.get('/lessons');
      const lessonsData = response.data.items || response.data;
      setLessons(Array.isArray(lessonsData) ? lessonsData : []);
    } catch (error) {
      console.error('Error fetching lessons:', error);
      setLessons([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/students');
      const studentsData = response.data.items || response.data;
      setStudents(Array.isArray(studentsData) ? studentsData : []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    }
  };

  const validateForm = () => {
    if (!formData.student_id) {
      toast.error('Выберите ученика');
      return false;
    }
    if (!formData.start_time || !formData.end_time) {
      toast.error('Выберите дату и время урока');
      return false;
    }
    if (new Date(formData.start_time) < new Date()) {
      toast.error('Урок не может начинаться в прошлом');
      return false;
    }
    if (new Date(formData.end_time) <= new Date(formData.start_time)) {
      toast.error('Время окончания должно быть позже времени начала');
      return false;
    }
    return true;
  };

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      const cleanTitle = formData.title.replace(/\s*\(\d+(\.\d+)?₽\)/g, '').trim();

      await apiClient.post('/lessons', {
        student_id: parseInt(formData.student_id),
        title: cleanTitle  || null,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        price: parseFloat(formData.price) || 0,
        notes: formData.notes || null,
      });
      toast.success('Урок создан');
      setShowModal(false);
      setFormData({
        student_id: '',
        title: '',
        start_time: '',
        end_time: '',
        price: '',
        notes: '',
      });
      fetchLessons();
    } catch (error: any) {
      console.error('Error creating lesson:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при создании урока');
    }
  };

  const openEditModal = () => {
    if (!selectedLesson) return;
    setEditData({
      title: selectedLesson.rawTitle.replace(/\s*\(\d+(\.\d+)?₽\)/g, '').trim(),
      price: String(selectedLesson.price || 0),
      notes: selectedLesson.notes || '',
      status: selectedLesson.status,
    });
    setShowLessonModal(false);
    setShowEditModal(true);
  };

  const handleUpdateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLesson) return;

    setSaving(true);
    try {
      const newPrice = parseFloat(editData.price) || 0;

      // Убираем возможные вхождения цены из title
      const cleanTitle = editData.title.replace(/\s*\(\d+(\.\d+)?₽\)/g, '').trim();

      await apiClient.put(`/lessons/${selectedLesson.id}`, {
        title: cleanTitle || null,
        price: newPrice,
        notes: editData.notes || null,
        status: editData.status,
      });
      toast.success('Урок обновлён');
      setShowEditModal(false);
      setSelectedLesson(null);
      fetchLessons();
    } catch (error: any) {
      console.error('Error updating lesson:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при обновлении урока');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLesson = async (lessonId: number) => {
    if (!confirm('Отменить урок? Деньги будут возвращены на баланс ученика.')) return;
    try {
      await apiClient.delete(`/lessons/${lessonId}`);
      toast.success('Урок отменён, деньги возвращены на баланс');
      setShowLessonModal(false);
      setShowEditModal(false);
      fetchLessons();
    } catch (error) {
      console.error('Error deleting lesson:', error);
      toast.error('Ошибка при отмене урока');
    }
  };

  const handleNavigate = (action: 'PREV' | 'NEXT' | 'TODAY') => {
    let newDate = new Date(currentDate);
    if (action === 'PREV') {
      if (currentView === Views.MONTH) newDate = subMonths(currentDate, 1);
      else if (currentView === Views.WEEK)
        newDate = new Date(currentDate.getTime() - 7 * 24 * 60 * 60 * 1000);
      else newDate = new Date(currentDate.getTime() - 24 * 60 * 60 * 1000);
    } else if (action === 'NEXT') {
      if (currentView === Views.MONTH) newDate = addMonths(currentDate, 1);
      else if (currentView === Views.WEEK)
        newDate = new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000);
      else newDate = new Date(currentDate.getTime() + 24 * 60 * 60 * 1000);
    } else if (action === 'TODAY') {
      newDate = new Date();
    }
    setCurrentDate(newDate);
  };

  const eventStyleGetter = (event: CalendarEvent) => {
    let backgroundColor = '#2e7d5e';
    if (event.status === 'cancelled') backgroundColor = '#c0392b';
    if (event.status === 'completed') backgroundColor = '#27ae60';

    return {
      style: {
        backgroundColor,
        borderRadius: '8px',
        border: 'none',
        color: 'white',
        padding: '4px 8px',
        fontSize: '12px',
      },
    };
  };

  const calendarEvents: CalendarEvent[] = Array.isArray(lessons)
  ? lessons.map((lesson) => {
      const cleanTitle = (lesson.title || 'Урок')
        .replace(/\s*\(\d+(\.\d+)?₽\)/g, '')
        .trim();

      return {
        id: lesson.id,
        title: isTeacher
          ? `${lesson.student_name || 'Ученик'}: ${cleanTitle} (${Number(lesson.price).toFixed(2)}₽)`
          : `${cleanTitle} (${Number(lesson.price).toFixed(2)}₽)`,
        rawTitle: cleanTitle,
        start: new Date(lesson.start_time),
        end: new Date(lesson.end_time),
        status: lesson.status,
        price: Number(lesson.price),
        notes: lesson.notes,
        student_name: lesson.student_name,
        student_id: lesson.student_id,
      };
    })
  : [];

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
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Расписание уроков</h1>
          {isTeacher && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
            >
              <FiPlus size={18} />
              <span>Создать урок</span>
            </button>
          )}
        </div>

        <div className="flex justify-between items-center mb-4 gap-2 flex-wrap">
          <div className="flex gap-2">
            <button
              onClick={() => handleNavigate('TODAY')}
              className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition flex items-center gap-2 text-sm"
            >
              <FiCalendarIcon size={16} />
              Сегодня
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleNavigate('PREV')}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition"
            >
              <FiChevronLeft size={20} />
            </button>
            <button
              onClick={() => handleNavigate('NEXT')}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition"
            >
              <FiChevronRight size={20} />
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentView(Views.MONTH)}
              className={`px-4 py-2 rounded-lg transition text-sm ${
                currentView === Views.MONTH
                  ? 'bg-accent text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Месяц
            </button>
            <button
              onClick={() => setCurrentView(Views.WEEK)}
              className={`px-4 py-2 rounded-lg transition text-sm ${
                currentView === Views.WEEK
                  ? 'bg-accent text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Неделя
            </button>
            <button
              onClick={() => setCurrentView(Views.DAY)}
              className={`px-4 py-2 rounded-lg transition text-sm ${
                currentView === Views.DAY
                  ? 'bg-accent text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              День
            </button>
          </div>
        </div>

        <div className="bg-dark-card rounded-xl p-4 border border-white/10">
          <Calendar
            localizer={localizer}
            events={calendarEvents}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 600 }}
            view={currentView}
            onView={(view) => setCurrentView(view)}
            date={currentDate}
            onNavigate={setCurrentDate}
            culture="ru"
            messages={{
              next: '',
              previous: '',
              today: '',
              month: '',
              week: '',
              day: '',
              agenda: '',
            }}
            eventPropGetter={eventStyleGetter}
            onSelectEvent={(event: CalendarEvent) => {
              setSelectedLesson(event);
              setShowLessonModal(true);
            }}
          />
        </div>

        {/* Модальное окно создания урока */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">Создать урок</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleCreateLesson} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Ученик *
                  </label>
                  <select
                    value={formData.student_id}
                    onChange={(e) =>
                      setFormData({ ...formData, student_id: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    required
                  >
                    <option value="">Выберите ученика</option>
                    {Array.isArray(students) &&
                      students.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Тема (необязательно)
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
                    Стоимость урока (₽)
                  </label>
                  <input
                    type="number"
                    step="100"
                    value={formData.price}
                    onChange={(e) =>
                      setFormData({ ...formData, price: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: 1000"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Оставьте 0 для бесплатного урока
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Заметки (необязательно)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData({ ...formData, notes: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Что нужно повторить, материалы..."
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
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition"
                  >
                    Создать
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Модальное окно информации об уроке */}
        {showLessonModal && selectedLesson && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">Информация об уроке</h2>
                <button
                  onClick={() => setShowLessonModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-gray-300">
                  <FiUser size={16} className="text-accent" />
                  <span>{selectedLesson.student_name || 'Ученик'}</span>
                </div>

                <div className="flex items-center gap-2 text-gray-300">
                  <FiCalendarIcon size={16} className="text-accent" />
                  <span>{selectedLesson.start.toLocaleDateString()}</span>
                </div>

                <div className="flex items-center gap-2 text-gray-300">
                  <FiClock size={16} className="text-accent" />
                  <span>
                    {selectedLesson.start.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}{' '}
                    -{' '}
                    {selectedLesson.end.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-gray-300">
                  <FiDollarSign size={16} className="text-accent" />
                  <span>{selectedLesson.price} ₽</span>
                </div>

                {selectedLesson.notes && (
                  <div className="mt-2 p-3 bg-gray-800 rounded-lg">
                    <p className="text-gray-400 text-sm">📝 {selectedLesson.notes}</p>
                  </div>
                )}

                <div className="flex items-center gap-2 text-gray-300">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      selectedLesson.status === 'scheduled'
                        ? 'bg-green-500/20 text-green-400'
                        : selectedLesson.status === 'cancelled'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}
                  >
                    {selectedLesson.status === 'scheduled'
                      ? 'Запланирован'
                      : selectedLesson.status === 'cancelled'
                      ? 'Отменён'
                      : 'Завершён'}
                  </span>
                </div>
              </div>
              
              

              <div className="flex justify-end gap-3 mt-6 flex-wrap">

                <button
                  onClick={() => {
                    setShowLessonModal(false);
                    navigate(`/lesson/${selectedLesson.id}`);
                  }}
                  className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
                >
                  <FiVideo size={14} />
                  Открыть урок
                </button>

                <button
                  onClick={() => setShowLessonModal(false)}
                  className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                >
                  Закрыть
                </button>
                {isTeacher && selectedLesson.status === 'scheduled' && (
                  <>
                    <button
                      onClick={openEditModal}
                      className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
                    >
                      <FiEdit2 size={14} />
                      Редактировать
                    </button>
                    <button
                      onClick={() => handleDeleteLesson(selectedLesson.id)}
                      className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white transition"
                    >
                      Отменить урок
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно редактирования урока */}
        {showEditModal && selectedLesson && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Редактировать урок
                </h2>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-white transition"
                >
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleUpdateLesson} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Тема
                  </label>
                  <input
                    type="text"
                    value={editData.title}
                    onChange={(e) =>
                      setEditData({ ...editData, title: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: Квадратные уравнения"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Стоимость урока (₽)
                  </label>
                  <input
                    type="number"
                    step="100"
                    value={editData.price}
                    onChange={(e) =>
                      setEditData({ ...editData, price: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  />
                  <p className="text-xs text-yellow-400 mt-1">
                    ⚠️ При изменении цены баланс ученика будет скорректирован автоматически.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Заметки
                  </label>
                  <textarea
                    value={editData.notes}
                    onChange={(e) =>
                      setEditData({ ...editData, notes: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Статус
                  </label>
                  <select
                    value={editData.status}
                    onChange={(e) =>
                      setEditData({ ...editData, status: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  >
                    <option value="scheduled">Запланирован</option>
                    <option value="completed">Завершён</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default CalendarPage;