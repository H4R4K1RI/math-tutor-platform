import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar: React.FC = () => {
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

        <nav className="hidden md:flex space-x-8">
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
    </header>
  );
};

export default Navbar;