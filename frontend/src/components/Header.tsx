import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiSun, FiMoon, FiMenu } from 'react-icons/fi';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode, onMenuClick }) => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-dark-card shadow-xl sticky top-0 z-50 border-b border-white/10">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <div className="flex items-center gap-3">
          {/* Кнопка меню - видна на всех устройствах */}
          {onMenuClick && (
            <button
              onClick={onMenuClick}
              className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition"
              aria-label="Открыть меню"
            >
              <FiMenu size={20} className="text-gray-700 dark:text-gray-300" />
            </button>
          )}
          <Link to="/" className="text-2xl font-bold text-primary tracking-tight">
            📐 Math<span className="text-accent">Tutor</span>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition"
            aria-label="Toggle theme"
          >
            {darkMode ? <FiSun className="text-yellow-400" size={18} /> : <FiMoon className="text-gray-700 dark:text-gray-300" size={18} />}
          </button>

          <nav className="hidden md:flex space-x-5">
            {user ? (
              <>
                <Link to="/dashboard" className="text-secondary hover:text-primary transition text-sm">Дашборд</Link>
                {isTeacher && (
                  <>
                    <Link to="/assignments" className="text-secondary hover:text-primary transition text-sm">Задания</Link>
                    <Link to="/review" className="text-secondary hover:text-primary transition text-sm">Проверка</Link>
                  </>
                )}
                <Link to="/chats" className="text-secondary hover:text-primary transition text-sm">Чаты</Link>
                <button onClick={handleLogout} className="text-secondary hover:text-danger transition text-sm">Выйти</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-secondary hover:text-primary transition text-sm">Вход</Link>
                <Link to="/register" className="text-secondary hover:text-primary transition text-sm">Регистрация</Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;