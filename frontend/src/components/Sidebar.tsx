import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiBook, FiCheckCircle, FiLogOut, FiSun, FiMoon, FiMessageCircle, FiX, FiUser,
         FiMail, FiUsers, FiFileText, FiDollarSign, FiCalendar, FiExternalLink, FiFolder,
         FiUserPlus, FiInbox } from 'react-icons/fi';
import apiClient from '../api/client';
import { socket } from '../socket';
import toast from 'react-hot-toast';

interface SidebarProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ darkMode, setDarkMode, isOpen, onClose }) => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);
  const [unreadCount, setUnreadCount] = useState(0);

  // Модалка "Добавить репетитора"
  const [showAddTutorModal, setShowAddTutorModal] = useState(false);
  const [inviteCode, setInviteCode] = useState('');
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const response = await apiClient.get('/chats');
      const chatsData = response.data.items || response.data;
      if (Array.isArray(chatsData)) {
        const totalUnread = chatsData.reduce((acc: number, chat: any) => acc + (chat.unread_count || 0), 0);
        setUnreadCount(totalUnread);
      } else {
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  useEffect(() => {
    if (!socket) return;

    fetchUnreadCount();

    // Дебаунс: не чаще раза в 2 секунды
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const debouncedFetch = () => {
      if (debounceTimer !== null) return;
      debounceTimer = setTimeout(() => {
        fetchUnreadCount();
        debounceTimer = null;
      }, 2000);
    };

    const onNewMessage = () => debouncedFetch();
    const onMessagesRead = () => debouncedFetch();
    const onChatCleared = () => debouncedFetch();
    const onChatDeleted = () => debouncedFetch();

    socket.on('new_message', onNewMessage);
    socket.on('messages_read', onMessagesRead);
    socket.on('chat_cleared', onChatCleared);
    socket.on('chat_deleted', onChatDeleted);

    return () => {
      if (socket) {
        socket.off('new_message', onNewMessage);
        socket.off('messages_read', onMessagesRead);
        socket.off('chat_cleared', onChatCleared);
        socket.off('chat_deleted', onChatDeleted);
      }
      if (debounceTimer !== null) {
        clearTimeout(debounceTimer);
      }
    };
  }, [socket]);

  // Обновляем счётчик при возврате на /chats
  useEffect(() => {
    if (location.pathname === '/chats') {
      fetchUnreadCount();
    }
  }, [location.pathname]);

  const handleLinkClick = () => {
    if (isMobile) onClose();
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleLinkClick();
  };

  const handleJoinByCode = async () => {
    if (!inviteCode.trim()) {
      toast.error('Введите код приглашения');
      return;
    }
    setJoining(true);
    try {
      // Поддерживаем и чистый код, и ссылку целиком
      const cleanCode = inviteCode
        .trim()
        .replace(/^.*[?&]invite=/, '')
        .replace(/^.*\/join\//, '');
      await apiClient.post(`/invitations/accept/${cleanCode}`);
      toast.success('Вы присоединились к репетитору!');
      setShowAddTutorModal(false);
      setInviteCode('');
      setTimeout(() => navigate('/chats'), 800);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Недействительный код');
    } finally {
      setJoining(false);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  const navLinkClass = (path: string) => `
    flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
    ${isActive(path)
      ? 'bg-accent text-white shadow-lg'
      : 'text-secondary hover:bg-hover hover:text-primary hover:translate-x-1'
    }
  `;

  return (
    <>
      {isOpen && isMobile && (
        <div className="fixed inset-0 bg-black/70 z-40 transition-opacity duration-300" onClick={onClose} />
      )}

      <aside className={`fixed top-0 left-0 h-full bg-card shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${isOpen ? 'translate-x-0' : '-translate-x-full'} w-72`}>
        <div className="p-6 border-b border-border flex justify-between items-center">
          <Link to={user ? '/dashboard' : '/'} onClick={handleLinkClick} className="text-2xl font-bold text-primary hover:text-accent transition">
            Math<span className="text-accent">Tutor</span>
          </Link>
          <button onClick={onClose} className="text-secondary hover:text-primary transition p-1" aria-label="Закрыть меню">
            <FiX size={20} />
          </button>
        </div>

        {user && (
          <div className="p-4 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                <FiUser size={20} className="text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-primary font-medium truncate">{user.full_name}</p>
                <div className="flex items-center gap-1 text-xs text-secondary">
                  <FiMail size={12} />
                  <span className="truncate">{user.email}</span>
                </div>
              </div>
            </div>
            <div className="mt-2">
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${isTeacher ? 'bg-accent/20 text-accent' : 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400'}`}>
                {isTeacher ? '👨‍🏫 Преподаватель' : '🧑‍🎓 Ученик'}
              </span>
            </div>
          </div>
        )}

        <nav className="flex-1 py-6 overflow-y-auto">
          <div className="space-y-1 px-4">
            {user && (
              <>
                {isTeacher && (
                  <>
                    <Link to="/profile" onClick={handleLinkClick} className={navLinkClass('/profile')}>
                      <FiUser size={20} />
                      <span>Профиль</span>
                    </Link>
                    <Link
                      to={`/tutor/${user?.id}`}
                      target="_blank"
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                    >
                      <FiExternalLink size={20} />
                      <span>Моя публичная карточка</span>
                    </Link>
                  </>
                )}

                <Link to="/dashboard" onClick={handleLinkClick} className={navLinkClass('/dashboard')}>
                  <FiHome size={20} />
                  <span>Дашборд</span>
                </Link>

                {isTeacher && (
                  <>
                    <Link to="/assignments" onClick={handleLinkClick} className={navLinkClass('/assignments')}>
                      <FiBook size={20} />
                      <span>Задания</span>
                    </Link>
                  </>
                )}
                {isTeacher ? (
                  <Link to="/tests" onClick={handleLinkClick} className={navLinkClass('/tests')}>
                    <FiFileText size={20} />
                    <span>Тесты</span>
                  </Link>
                ) : (
                  <Link to="/my-tests" onClick={handleLinkClick} className={navLinkClass('/my-tests')}>
                    <FiFileText size={20} />
                    <span>Тесты</span>
                  </Link>
                )}
                {isTeacher && (
                  <>
                    <Link to="/review" onClick={handleLinkClick} className={navLinkClass('/review')}>
                      <FiCheckCircle size={20} />
                      <span>Проверка решений</span>
                    </Link>
                    <Link to="/groups" onClick={handleLinkClick} className={navLinkClass('/groups')}>
                      <FiUsers size={20} />
                      <span>Группы</span>
                    </Link>
                    <Link to="/students" onClick={handleLinkClick} className={navLinkClass('/students')}>
                      <FiUsers size={20} />
                      <span>Ученики</span>
                    </Link>
                    <Link to="/requests" onClick={handleLinkClick} className={navLinkClass('/requests')}>
                      <FiCalendar size={20} />
                      <span>Заявки на уроки</span>
                    </Link>
                    <Link to="/tutoring-requests" onClick={handleLinkClick} className={navLinkClass('/tutoring-requests')}>
                      <FiInbox size={20} />
                      <span>Заявки на обучение</span>
                    </Link>
                    <Link to="/finance" onClick={handleLinkClick} className={navLinkClass('/finance')}>
                      <FiDollarSign size={20} />
                      <span>Финансы</span>
                    </Link>
                  </>
                )}
                <Link to="/calendar" onClick={handleLinkClick} className={navLinkClass('/calendar')}>
                  <FiCalendar size={20} />
                  <span>Расписание</span>
                </Link>
                <Link to="/chats" onClick={handleLinkClick} className={navLinkClass('/chats')}>
                  <FiMessageCircle size={20} />
                  <span>Чаты</span>
                  {unreadCount > 0 && (
                    <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
                </Link>
                <Link to="/materials" onClick={handleLinkClick} className={navLinkClass('/materials')}>
                  <FiFolder size={20} />
                  <span>Библиотека</span>
                </Link>

                {!isTeacher && (
                  <>
                    <Link to="/payments" onClick={handleLinkClick} className={navLinkClass('/payments')}>
                      <FiDollarSign size={20} />
                      <span>Мои платежи</span>
                    </Link>
                    <Link to="/requests" onClick={handleLinkClick} className={navLinkClass('/requests')}>
                      <FiCalendar size={20} />
                      <span>Мои заявки</span>
                    </Link>
                    <button
                      onClick={() => { setShowAddTutorModal(true); handleLinkClick(); }}
                      className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-secondary hover:bg-hover hover:text-primary transition-all duration-200"
                    >
                      <FiUserPlus size={20} />
                      <span>Добавить репетитора</span>
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </nav>

        <div className="p-6 border-t border-border space-y-3">
          <button onClick={() => setDarkMode(!darkMode)} className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-secondary bg-hover hover:bg-hover hover:text-primary transition-all duration-200">
            {darkMode ? <FiSun size={20} className="text-yellow-500" /> : <FiMoon size={20} />}
            <span>{darkMode ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>
          {user && (
            <button onClick={handleLogout} className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-secondary bg-hover hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 transition-all duration-200">
              <FiLogOut size={20} /><span>Выйти</span>
            </button>
          )}
        </div>
      </aside>

      {/* Модалка "Добавить репетитора" */}
      {showAddTutorModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
          <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">Добавить репетитора</h2>
            <p className="text-gray-400 text-sm mb-4">
              Введите код приглашения или вставьте ссылку целиком.
            </p>
            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder="Код или ссылка"
              className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white mb-4"
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowAddTutorModal(false); setInviteCode(''); }}
                className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
              >
                Отмена
              </button>
              <button
                onClick={handleJoinByCode}
                disabled={joining || !inviteCode.trim()}
                className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
              >
                {joining ? 'Присоединяемся...' : 'Присоединиться'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;