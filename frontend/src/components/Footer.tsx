import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white dark:bg-[#0d1b12] border-t border-gray-200 dark:border-gray-700 py-6 mt-auto">
      <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
        <p>© 2026 Math Tutor Platform. Все права защищены.</p>
        <div className="flex justify-center gap-4 mt-2">
          <Link to="/privacy" className="hover:text-[#2e7d5e] transition">
            Политика конфиденциальности
          </Link>
          <Link to="/contacts" className="hover:text-[#2e7d5e] transition">
            Контакты
          </Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
