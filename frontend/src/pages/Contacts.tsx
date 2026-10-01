import React from 'react';
import { Link } from 'react-router-dom';
import { FiMail, FiSend, FiGithub, FiMessageCircle, FiMapPin, FiClock } from 'react-icons/fi';
import AnimatedPage from '../components/AnimatedPage';

const Contacts: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-dark-card rounded-2xl shadow-xl p-8 border border-white/10">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2 text-primary">Контакты</h1>
            <p className="text-secondary">Свяжитесь с нами любым удобным способом</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Telegram */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-dark-bg border border-white/10 hover:border-accent transition">
              <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                <FiSend size={24} className="text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-primary">Telegram</h3>
                <a href="https://t.me/har4k1ri" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                  @har4k1ri
                </a>
              </div>
            </div>

            {/* Email */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-dark-bg border border-white/10 hover:border-accent transition">
              <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                <FiMail size={24} className="text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-primary">Email</h3>
                <a href="mailto:bokhirzhon010206@gmail.com" className="text-accent hover:underline">
                  bokhirzhon010206@gmail.com
                </a>
              </div>
            </div>

            {/* GitHub */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-dark-bg border border-white/10 hover:border-accent transition">
              <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                <FiGithub size={24} className="text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-primary">GitHub</h3>
                <a href="https://github.com/H4R4K1RI" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                  github.com/H4R4K1RI
                </a>
              </div>
            </div>

            {/* Чат на сайте */}
            <div className="flex items-center gap-4 p-4 rounded-xl bg-dark-bg border border-white/10 hover:border-accent transition">
              <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                <FiMessageCircle size={24} className="text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-primary">Чат на сайте</h3>
                <Link to="/chats" className="text-accent hover:underline">
                  Написать в чат →
                </Link>
              </div>
            </div>
          </div>

          {/* Дополнительная информация */}
          <div className="mt-8 p-6 rounded-xl bg-dark-bg border border-white/10">
            <h3 className="font-semibold text-primary mb-4">📋 Обратите внимание</h3>
            <ul className="space-y-2 text-secondary">
              <li className="flex items-center gap-2">
                <FiClock className="text-accent" />
                <span>Время ответа: обычно в течение 24 часов</span>
              </li>
              <li className="flex items-center gap-2">
                <FiMapPin className="text-accent" />
                <span>Разработчик: Мирхабибов Бохиржон Алишерович</span>
              </li>
            </ul>
          </div>

          {/* Кнопка возврата */}
          <div className="mt-6 text-center">
            <Link to="/dashboard" className="text-accent hover:underline">← Вернуться на главную</Link>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default Contacts;