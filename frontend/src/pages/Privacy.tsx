import React from 'react';
import { Link } from 'react-router-dom';
import AnimatedPage from '../components/AnimatedPage';

const Privacy: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-dark-card rounded-2xl shadow-xl p-8 border border-white/10">
          <h1 className="text-3xl font-bold mb-6 text-primary text-center">Политика конфиденциальности</h1>
          
          <div className="space-y-6 text-secondary">
            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">1. Общие положения</h2>
              <p>Настоящая Политика конфиденциальности (далее — «Политика») описывает, какие данные собирает и обрабатывает платформа Math Tutor Platform (далее — «Платформа»), а также цели и способы их использования.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">2. Какие данные мы собираем</h2>
              <p>При регистрации на Платформе вы указываете:</p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Адрес электронной почты</li>
                <li>Полное имя</li>
                <li>Пароль (хранится в зашифрованном виде с использованием bcrypt)</li>
              </ul>
              <p className="mt-2">Также мы автоматически собираем техническую информацию: IP-адрес, тип браузера, время доступа.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">3. Как мы используем ваши данные</h2>
              <ul className="list-disc pl-6 space-y-1">
                <li>Для создания и управления вашим аккаунтом</li>
                <li>Для предоставления доступа к заданиям и решениям</li>
                <li>Для общения в чате с учителем/учеником</li>
                <li>Для отправки уведомлений о новых сообщениях (с вашего согласия)</li>
                <li>Для улучшения работы Платформы</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">4. Передача данных третьим лицам</h2>
              <p>Мы не передаём ваши персональные данные третьим лицам, за исключением случаев, предусмотренных законодательством РФ.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">5. Хранение и защита данных</h2>
              <p>Ваши данные хранятся на защищённых серверах в России. Мы используем современные методы защиты информации:</p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>Шифрование HTTPS (SSL/TLS)</li>
                <li>Хэширование паролей (bcrypt)</li>
                <li>JWT токены в HttpOnly cookies</li>
                <li>Регулярные обновления безопасности</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">6. Ваши права</h2>
              <ul className="list-disc pl-6 space-y-1">
                <li>Просматривать и редактировать свои данные в профиле</li>
                <li>Запросить удаление всех своих данных</li>
                <li>Отозвать согласие на обработку данных</li>
              </ul>
              <p className="mt-2">Для этого напишите нам на email: <a href="mailto:bokhirzhon010206@gmail.com" className="text-accent hover:underline">bokhirzhon010206@gmail.com</a></p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">7. Изменения в Политике</h2>
              <p>Мы оставляем за собой право вносить изменения в настоящую Политику. Актуальная версия всегда доступна по этому адресу. Изменения вступают в силу с момента их публикации.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-3 text-primary">8. Контактная информация</h2>
              <p>По всем вопросам, связанным с обработкой персональных данных, вы можете связаться с нами:</p>
              <ul className="list-disc pl-6 mt-2">
                <li>Email: <a href="mailto:bokhirzhon010206@gmail.com" className="text-accent hover:underline">bokhirzhon010206@gmail.com</a></li>
                <li>Telegram: <a href="https://t.me/har4k1ri" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">@har4k1ri</a></li>
                <li>GitHub: <a href="https://github.com/H4R4K1RI" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">github.com/H4R4K1RI</a></li>
              </ul>
            </section>

            <p className="text-sm text-muted pt-4 border-t border-white/10">Дата последнего обновления: 23 апреля 2026 года</p>
          </div>
          
          <div className="mt-8 text-center">
            <Link to="/dashboard" className="text-accent hover:underline">← Вернуться на главную</Link>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default Privacy;