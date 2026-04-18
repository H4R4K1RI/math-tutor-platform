import React from 'react';
import { Link } from 'react-router-dom';

const Contacts: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6 dark:text-white">Контакты</h1>
      
      <div className="bg-white dark:bg-[#1a1a1a] rounded-lg shadow p-6 space-y-4">
        <p className="text-gray-700 dark:text-gray-300">
          По всем вопросам вы можете связаться со мной:
        </p>
        
        <div className="space-y-2">
          <p>
            <span className="font-semibold">📧 Email:</span>{' '}
            <a href="mailto:bokhirzhon010206@gmail.com" className="text-[#2e7d5e] hover:underline">
              bokhirzhon010206@gmail.com
            </a>
          </p>
          <p>
            <span className="font-semibold">📱 Telegram:</span>{' '}
            <a href="https://t.me/har4k1ri" target="_blank" rel="noopener noreferrer" className="text-[#2e7d5e] hover:underline">
              @har4k1ri
            </a>
          </p>
          <p>
            <span className="font-semibold">💻 GitHub:</span>{' '}
            <a href="https://github.com/H4R4K1RI" target="_blank" rel="noopener noreferrer" className="text-[#2e7d5e] hover:underline">
              github.com/H4R4K1RI
            </a>
          </p>
        </div>
        
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Обычно отвечаю в течение 24 часов.
          </p>
        </div>
      </div>
      
      <div className="mt-8">
        <Link to="/" className="text-[#2e7d5e] hover:underline">← Вернуться на главную</Link>
      </div>
    </div>
  );
};

export default Contacts;
