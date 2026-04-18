import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Header: React.FC = () => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white dark:bg-[#0d1b12] shadow-md sticky top-0 z-40">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-[#2e7d5e] dark:text-[#4a9b6e]">
          📐 Math Tutor
        </Link>

        <nav className="hidden md:flex space-x-6">
          {user ? (
            <>
              <Link to="/dashboard" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                Дашборд
              </Link>
              {isTeacher && (
                <>
                  <Link to="/assignments" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                    Задания
                  </Link>
                  <Link to="/review" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                    Проверка
                  </Link>
                </>
              )}
              <Link to="/chats" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                Чаты
              </Link>
              <button onClick={handleLogout} className="text-gray-700 dark:text-gray-300 hover:text-red-500 transition">
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                Вход
              </Link>
              <Link to="/register" className="text-gray-700 dark:text-gray-300 hover:text-[#2e7d5e] transition">
                Регистрация
              </Link>
            </>
          )}
        </nav>

        {/* Мобильное меню (гамбургер) — можно добавить позже */}
        <div className="md:hidden">
          {/* Здесь будет мобильное меню, пока пусто */}
        </div>
      </div>
    </header>
  );
};

export default Header;
