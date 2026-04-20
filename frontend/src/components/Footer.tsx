import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <footer className="bg-dark-card border-t border-white/10 py-6 mt-auto">
      <div className="container mx-auto px-6 text-center text-sm text-gray-400">
        <p>© 2026 Math Tutor Platform. Все права защищены.</p>
        <div className="flex justify-center gap-4 mt-2">
          <Link to="/privacy" className="hover:text-accent transition">Политика конфиденциальности</Link>
          <Link to="/contacts" className="hover:text-accent transition">Контакты</Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;