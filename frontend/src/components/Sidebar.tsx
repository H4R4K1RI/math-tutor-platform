import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiBook, FiCheckCircle, FiLogOut, FiSun, FiMoon, FiMessageCircle, FiX, FiUser, FiMail } from 'react-icons/fi';

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

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLinkClick = () => {
    if (isMobile) {
      onClose();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleLinkClick();
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navLinkClass = (path: string) => `
    flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
    ${isActive(path) 
      ? 'bg-accent text-white shadow-lg' 
      : 'text-secondary hover:bg-hover hover:text-primary hover:translate-x-1'
    }
  `;

  return (
    <>
      {/* Оверлей для мобильных */}
      {isOpen && isMobile && (
        <div 
          className="fixed inset-0 bg-black/70 z-40 transition-opacity duration-300" 
          onClick={onClose} 
        />
      )}

      {/* Сайдбар */}
      <aside className={`
        fixed top-0 left-0 h-full bg-card shadow-2xl z-50 
        transform transition-transform duration-300 ease-in-out
        flex flex-col
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        w-72
      `}>
        {/* Логотип и кнопка закрытия */}
        <div className="p-6 border-b border-border flex justify-between items-center">
          <Link 
            to="/" 
            onClick={handleLinkClick} 
            className="text-2xl font-bold text-primary hover:text-accent transition"
          >
            Math<span className="text-accent">Tutor</span>
          </Link>
          {/* Кнопка закрытия - для всех устройств */}
          <button 
            onClick={onClose} 
            className="text-secondary hover:text-primary transition p-1"
            aria-label="Закрыть меню"
            title="Свернуть меню"
          >
            <FiX size={20} />
          </button>
        </div>

        {/* Информация о пользователе */}
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
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                isTeacher 
                  ? 'bg-accent/20 text-accent' 
                  : 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400'
              }`}>
                {isTeacher ? '👨‍🏫 Преподаватель' : '🧑‍🎓 Ученик'}
              </span>
            </div>
          </div>
        )}

        {/* Навигация */}
        <nav className="flex-1 py-6 overflow-y-auto">
          <div className="space-y-1 px-4">
            {user && (
              <>
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
                    <Link to="/review" onClick={handleLinkClick} className={navLinkClass('/review')}>
                      <FiCheckCircle size={20} />
                      <span>Проверка решений</span>
                    </Link>
                  </>
                )}

                <Link to="/chats" onClick={handleLinkClick} className={navLinkClass('/chats')}>
                  <FiMessageCircle size={20} />
                  <span>Чаты</span>
                </Link>
              </>
            )}
          </div>
        </nav>

        {/* Нижняя панель с кнопками */}
        <div className="p-6 border-t border-border space-y-3">
          <button 
            onClick={() => setDarkMode(!darkMode)} 
            className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-secondary bg-hover hover:bg-hover hover:text-primary transition-all duration-200"
          >
            {darkMode ? <FiSun size={20} className="text-yellow-500" /> : <FiMoon size={20} />}
            <span>{darkMode ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>

          {user && (
            <button 
              onClick={handleLogout} 
              className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-secondary bg-hover hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 transition-all duration-200"
            >
              <FiLogOut size={20} />
              <span>Выйти</span>
            </button>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;