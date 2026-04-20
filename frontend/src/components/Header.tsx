import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiSun, FiMoon } from 'react-icons/fi';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode }) => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-dark-card shadow-xl sticky top-0 z-50 border-b border-white/10">
      <div className="container mx-auto px-6 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-primary tracking-tight">
          📐 Math<span className="text-accent">Tutor</span>
        </Link>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 transition"
            aria-label="Toggle theme"
          >
            {darkMode ? <FiSun className="text-yellow-400" size={20} /> : <FiMoon className="text-gray-700 dark:text-gray-300" size={20} />}
          </button>

          <nav className="hidden md:flex space-x-6">
            {user ? (
              <>
                <Link to="/dashboard" className="text-secondary hover:text-primary transition">Дашборд</Link>
                {isTeacher && (
                  <>
                    <Link to="/assignments" className="text-secondary hover:text-primary transition">Задания</Link>
                    <Link to="/review" className="text-secondary hover:text-primary transition">Проверка</Link>
                  </>
                )}
                <Link to="/chats" className="text-secondary hover:text-primary transition">Чаты</Link>
                <button onClick={handleLogout} className="text-secondary hover:text-danger transition">Выйти</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-secondary hover:text-primary transition">Вход</Link>
                <Link to="/register" className="text-secondary hover:text-primary transition">Регистрация</Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;