import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiBook, FiCheckCircle, FiLogOut, FiSun, FiMoon, FiMessageCircle } from 'react-icons/fi';

interface SidebarProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ darkMode, setDarkMode, isOpen, onClose }) => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    onClose();
  };

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={onClose} />
      )}

      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white dark:bg-[#0d1b12] text-gray-800 dark:text-gray-200 shadow-xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-5 border-b border-gray-200 dark:border-gray-700">
          <Link
  to="/"
  onClick={onClose}
  className="text-xl font-bold block text-center text-[#2e7d5e] dark:text-[#2e7d5e]"
>
  📐 Math Tutor
</Link>
        </div>

        <nav className="flex-1 py-6">
          <div className="space-y-1">
            {user && (
              <>
                <Link
                  to="/dashboard"
                  onClick={onClose}
                  className="flex items-center gap-3 px-5 py-3 hover:bg-gray-100 dark:hover:bg-[#1e2a1a] transition rounded-lg"
                >
                  <FiHome size={20} />
                  <span>Дашборд</span>
                </Link>

                {isTeacher && (
                  <>
                    <Link
                      to="/assignments"
                      onClick={onClose}
                      className="flex items-center gap-3 px-5 py-3 hover:bg-gray-100 dark:hover:bg-[#1e2a1a] transition rounded-lg"
                    >
                      <FiBook size={20} />
                      <span>Задания</span>
                    </Link>
                    <Link
                      to="/review"
                      onClick={onClose}
                      className="flex items-center gap-3 px-5 py-3 hover:bg-gray-100 dark:hover:bg-[#1e2a1a] transition rounded-lg"
                    >
                      <FiCheckCircle size={20} />
                      <span>Проверка решений</span>
                    </Link>
                  </>
                )}

                <Link to="/chats" onClick={onClose} className="flex items-center gap-3 px-5 py-3 hover:bg-gray-100 dark:hover:bg-[#1e2a1a] transition rounded-lg">
                  <FiMessageCircle size={20} />
                  <span>Чаты</span>
                </Link>
              </>
            )}
          </div>
        </nav>

        <div className="p-5 border-t border-gray-200 dark:border-gray-700 space-y-2">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="flex items-center gap-3 px-3 py-2 w-full hover:bg-gray-100 dark:hover:bg-[#1e2a1a] rounded-lg transition"
          >
            {darkMode ? <FiSun size={20} /> : <FiMoon size={20} />}
            <span>{darkMode ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>

          {user && (
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2 w-full hover:bg-gray-100 dark:hover:bg-[#1e2a1a] rounded-lg transition"
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
