import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

const Navbar: React.FC<NavbarProps> = ({ darkMode, setDarkMode }) => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-600 dark:bg-gray-800 text-white p-4 shadow-md transition-colors">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">📐 Math Tutor</Link>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="text-white hover:text-blue-200 transition text-xl"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>

          {user ? (
            <>
              <span>Привет, {user.full_name.split(' ')[0]}</span>
              {isTeacher && (
                <>
                  <Link to="/assignments" className="hover:underline">Задания</Link>
                  <Link to="/review" className="hover:underline">Проверка решений</Link>
                </>
              )}
              <Link to="/dashboard" className="hover:underline">Дашборд</Link>
              <button onClick={handleLogout} className="hover:underline">Выйти</button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:underline">Вход</Link>
              <Link to="/register" className="hover:underline">Регистрация</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;