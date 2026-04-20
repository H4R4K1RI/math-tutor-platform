import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiBook, FiCheckCircle, FiLogOut, FiSun, FiMoon, FiMessageCircle, FiX } from 'react-icons/fi';

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
      {isOpen && <div className="fixed inset-0 bg-black/70 z-40 lg:hidden" onClick={onClose} />}

      <aside className={`fixed top-0 left-0 h-full w-72 bg-dark-card shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <Link to="/" onClick={onClose} className="text-2xl font-bold text-white">
            Math<span className="text-accent">Tutor</span>
          </Link>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition">
            <FiX size={24} />
          </button>
        </div>

        <nav className="flex-1 py-8">
          <div className="space-y-2 px-4">
            {user && (
              <>
                <Link to="/dashboard" onClick={onClose} className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 hover:text-white transition">
                  <FiHome size={20} />
                  <span>Дашборд</span>
                </Link>

                {isTeacher && (
                  <>
                    <Link to="/assignments" onClick={onClose} className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 hover:text-white transition">
                      <FiBook size={20} />
                      <span>Задания</span>
                    </Link>
                    <Link to="/review" onClick={onClose} className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 hover:text-white transition">
                      <FiCheckCircle size={20} />
                      <span>Проверка решений</span>
                    </Link>
                  </>
                )}

                <Link to="/chats" onClick={onClose} className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/10 hover:text-white transition">
                  <FiMessageCircle size={20} />
                  <span>Чаты</span>
                </Link>
              </>
            )}
          </div>
        </nav>

        <div className="p-6 border-t border-white/10 space-y-4">
          <button onClick={() => setDarkMode(!darkMode)} className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-gray-300 hover:bg-white/10 transition">
            {darkMode ? <FiSun size={20} /> : <FiMoon size={20} />}
            <span>{darkMode ? 'Светлая тема' : 'Тёмная тема'}</span>
          </button>

          {user && (
            <button onClick={handleLogout} className="flex items-center gap-3 w-full px-4 py-2 rounded-xl text-gray-300 hover:bg-danger/20 hover:text-danger transition">
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