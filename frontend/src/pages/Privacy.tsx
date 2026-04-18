import React from 'react';
import { Link } from 'react-router-dom';

const Privacy: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 dark:text-white">Политика конфиденциальности</h1>
      
      <div className="space-y-6 text-gray-700 dark:text-gray-300">
        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">1. Общие положения</h2>
          <p>Настоящий сайт (далее — «Сайт») уважает ваше право на конфиденциальность. Эта Политика описывает, какие данные мы собираем, как их используем и защищаем.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">2. Какие данные мы собираем</h2>
          <p>При регистрации на Сайте вы указываете:</p>
          <ul className="list-disc pl-6 mt-2 space-y-1">
            <li>Адрес электронной почты</li>
            <li>Полное имя</li>
            <li>Пароль (хранится в зашифрованном виде)</li>
          </ul>
          <p className="mt-2">Эти данные необходимы для идентификации пользователя и обеспечения работы платформы.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">3. Как мы используем данные</h2>
          <p>Ваши данные используются только для:</p>
          <ul className="list-disc pl-6 mt-2 space-y-1">
            <li>Создания и управления заданиями и решениями</li>
            <li>Общения в чате с учителем</li>
            <li>Отправки уведомлений (если вы подписаны)</li>
          </ul>
          <p className="mt-2">Мы не передаём ваши данные третьим лицам.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">4. Хранение и защита данных</h2>
          <p>Все данные хранятся на защищённых серверах в России. Мы используем современные методы защиты (HTTPS, шифрование паролей).</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">5. Ваши права</h2>
          <p>Вы можете в любой момент запросить удаление всех ваших данных, написав нам на почту: <a href="mailto:bokhirzhon010206@gmail.com" className="text-[#2e7d5e] hover:underline">bokhirzhon010206@gmail.com</a>.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">6. Контактная информация</h2>
          <p>По всем вопросам, связанным с персональными данными, вы можете связаться с нами:</p>
          <ul className="list-disc pl-6 mt-2">
            <li>Email: bokhirzhon010206@gmail.com</li>
            <li>Telegram: @har4k1ri</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-2 dark:text-white">7. Изменения в Политике</h2>
          <p>Мы оставляем за собой право вносить изменения в настоящую Политику. Актуальная версия всегда доступна по этому адресу.</p>
        </section>

        <p className="text-sm text-gray-500 pt-4">Дата последнего обновления: 14 апреля 2026 года</p>
      </div>
      
      <div className="mt-8">
        <Link to="/" className="text-[#2e7d5e] hover:underline">← Вернуться на главную</Link>
      </div>
    </div>
  );
};

export default Privacy;
