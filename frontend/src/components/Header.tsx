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
        <Link to="/" className="text-2xl font-bold text-white tracking-tight">
          📐 Math<span className="text-accent">Tutor</span>
        </Link>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition"
            aria-label="Toggle theme"
          >
            {darkMode ? <FiSun className="text-yellow-400" size={20} /> : <FiMoon className="text-gray-300" size={20} />}
          </button>

          <nav className="hidden md:flex space-x-6">
            {user ? (
              <>
                <Link to="/dashboard" className="text-gray-300 hover:text-white transition">Дашборд</Link>
                {isTeacher && (
                  <>
                    <Link to="/assignments" className="text-gray-300 hover:text-white transition">Задания</Link>
                    <Link to="/review" className="text-gray-300 hover:text-white transition">Проверка</Link>
                  </>
                )}
                <Link to="/chats" className="text-gray-300 hover:text-white transition">Чаты</Link>
                <button onClick={handleLogout} className="text-gray-300 hover:text-danger transition">Выйти</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-300 hover:text-white transition">Вход</Link>
                <Link to="/register" className="text-gray-300 hover:text-white transition">Регистрация</Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;