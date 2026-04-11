import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar: React.FC = () => {
  const { user, logout, isTeacher } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-gradient-to-r from-blue-700 to-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-3">
        <div className="flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold flex items-center gap-2">
            📐 Math Tutor
          </Link>
          
          {/* Десктопное меню */}
          <div className="hidden md:flex items-center space-x-4">
            {user ? (
              <>
                <span className="text-sm bg-blue-500 px-3 py-1 rounded-full">
                  👋 {user.full_name.split(' ')[0]}
                </span>
                {isTeacher && (
                  <>
                    <Link to="/assignments" className="hover:text-blue-200 transition">📋 Задания</Link>
                    <Link to="/review" className="hover:text-blue-200 transition">✅ Проверка</Link>
                  </>
                )}
                <Link to="/dashboard" className="hover:text-blue-200 transition">📊 Дашборд</Link>
                <button onClick={handleLogout} className="bg-white text-blue-600 px-3 py-1 rounded-lg hover:bg-blue-100 transition">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-blue-200 transition">Вход</Link>
                <Link to="/register" className="bg-white text-blue-600 px-3 py-1 rounded-lg hover:bg-blue-100 transition">
                  Регистрация
                </Link>
              </>
            )}
          </div>
          
          {/* Кнопка гамбургера для мобильных */}
          <button 
            className="md:hidden text-white focus:outline-none"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
        
        {/* Мобильное меню */}
        {isMenuOpen && (
          <div className="md:hidden mt-3 pt-3 border-t border-blue-500 space-y-2">
            {user ? (
              <>
                <div className="text-sm bg-blue-500 px-3 py-1 rounded-full inline-block">
                  👋 {user.full_name.split(' ')[0]}
                </div>
                {isTeacher && (
                  <>
                    <Link to="/assignments" className="block hover:text-blue-200 transition py-1">📋 Задания</Link>
                    <Link to="/review" className="block hover:text-blue-200 transition py-1">✅ Проверка</Link>
                  </>
                )}
                <Link to="/dashboard" className="block hover:text-blue-200 transition py-1">📊 Дашборд</Link>
                <button onClick={handleLogout} className="block w-full text-left bg-white text-blue-600 px-3 py-1 rounded-lg hover:bg-blue-100 transition">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="block hover:text-blue-200 transition py-1">Вход</Link>
                <Link to="/register" className="block bg-white text-blue-600 px-3 py-1 rounded-lg hover:bg-blue-100 transition">
                  Регистрация
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;