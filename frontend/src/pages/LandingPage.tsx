import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FiBook, FiMessageCircle, FiVideo, FiBarChart2, 
  FiUsers, FiTrendingUp, FiCheckCircle, FiChevronRight,
  FiStar, FiArrowRight, FiPlay, FiZap, FiShield
} from 'react-icons/fi';

const LandingPage: React.FC = () => {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  const [visibleSections, setVisibleSections] = useState({
    features: false,
    steps: false,
    pricing: false,
  });

  const featuresRef = useRef<HTMLDivElement>(null);
  const stepsRef = useRef<HTMLDivElement>(null);
  const pricingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute('data-section');
            if (id) {
              setVisibleSections((prev) => ({ ...prev, [id]: true }));
            }
          }
        });
      },
      { threshold: 0.2 }
    );

    if (featuresRef.current) observer.observe(featuresRef.current);
    if (stepsRef.current) observer.observe(stepsRef.current);
    if (pricingRef.current) observer.observe(pricingRef.current);

    return () => observer.disconnect();
  }, []);

  const faqItems = [
    {
      question: 'Нужно ли устанавливать программу?',
      answer: 'Нет, достаточно браузера. Платформа работает онлайн, ничего устанавливать не нужно.'
    },
    {
      question: 'Есть ли бесплатный тариф?',
      answer: 'Да, бесплатный тариф включает до 5 учеников и 10 заданий в месяц. Этого достаточно для старта.'
    },
    {
      question: 'Можно ли проводить групповые занятия?',
      answer: 'Да, есть функция "Группы учеников". Вы можете создавать группы и назначать задания сразу всем ученикам.'
    },
    {
      question: 'Подходит ли для других предметов?',
      answer: 'Да, платформа универсальна. Подходит для математики, физики, английского, программирования и любых других предметов.'
    },
    {
      question: 'Как ученики получают доступ?',
      answer: 'Вы отправляете ссылку-приглашение, ученик регистрируется и автоматически привязывается к вам.'
    }
  ];

  const steps = [
    { number: '01', title: 'Регистрация', desc: 'Создайте аккаунт за 2 минуты' },
    { number: '02', title: 'Создание задания', desc: 'Добавьте описание, файлы, установите дедлайн' },
    { number: '03', title: 'Ученик решает', desc: 'Ученик получает задание и отправляет решение' },
    { number: '04', title: 'Проверка', desc: 'Проверьте, оставьте фидбек, поставьте статус' },
  ];

  const testimonials = [
    {
      name: 'Александр Петров',
      role: 'Репетитор по математике, 5 лет опыта',
      text: 'Платформа изменила мой подход к преподаванию. Ученики стали более организованными, а я экономлю около 5 часов в неделю на проверке заданий.',
      rating: 5
    },
    {
      name: 'Елена Смирнова',
      role: 'Репетитор по английскому языку',
      text: 'Чат в реальном времени и удобная отправка решений — мои ученики всегда на связи. Очень удобно, что всё в одном месте.',
      rating: 5
    },
    {
      name: 'Михаил Иванов',
      role: 'Репетиторский центр "Знание"',
      text: 'Используем платформу для всей нашей команды из 4 преподавателей. Удобное управление группами и общая база учеников.',
      rating: 5
    }
  ];

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <header className="bg-dark-card border-b border-white/10 sticky top-0 z-50 backdrop-blur-sm bg-dark-card/95">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-bold text-white">
            Math<span className="text-accent">Tutor</span>
          </Link>
          
          <nav className="hidden md:flex gap-6">
            <button onClick={() => scrollToSection('features')} className="text-gray-300 hover:text-white transition">Возможности</button>
            <button onClick={() => scrollToSection('steps')} className="text-gray-300 hover:text-white transition">Как работает</button>
            <button onClick={() => scrollToSection('pricing')} className="text-gray-300 hover:text-white transition">Тарифы</button>
            <button onClick={() => scrollToSection('faq')} className="text-gray-300 hover:text-white transition">FAQ</button>
          </nav>
          
          <div className="flex gap-3">
            <Link to="/login" className="px-4 py-2 rounded-lg border border-accent text-accent hover:bg-accent hover:text-white transition">
              Вход
            </Link>
            <Link to="/register" className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition">
              Регистрация
            </Link>
          </div>
        </div>
      </header>

      {/* Hero секция */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="animate-fade-in-up">
          <div className="inline-flex items-center gap-2 bg-accent/10 rounded-full px-4 py-1 mb-6">
            <FiZap className="text-accent" size={14} />
            <span className="text-accent text-sm font-medium">Новая версия 2.0</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Всё для онлайн-обучения в <span className="text-accent">одном месте</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
            Задания, чат, онлайн-уроки, статистика — платформа, которая экономит время репетитора
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/register" className="px-8 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium text-lg transition flex items-center gap-2">
              Начать бесплатно <FiArrowRight />
            </Link>
            <button onClick={() => scrollToSection('features')} className="px-8 py-3 rounded-lg border border-white/20 text-white hover:bg-white/10 transition flex items-center gap-2">
              Узнать больше
            </button>
          </div>
        </div>

        {/* Социальное доказательство */}
        <div className="flex flex-wrap justify-center gap-8 mt-16">
          <div className="text-center">
            <div className="text-2xl font-bold text-accent">500+</div>
            <div className="text-sm text-gray-400">учеников</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-accent">100+</div>
            <div className="text-sm text-gray-400">репетиторов</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-accent">2000+</div>
            <div className="text-sm text-gray-400">уроков</div>
          </div>
        </div>
      </section>

      {/* Возможности */}
      <section id="features" ref={featuresRef} data-section="features" className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">Все инструменты для репетитора</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon: FiBook, title: 'Задания и решения', desc: 'Создавайте задания, прикрепляйте файлы, проверяйте решения и оставляйте фидбек' },
            { icon: FiMessageCircle, title: 'Чат в реальном времени', desc: 'Общайтесь с учениками, обсуждайте задания, получайте уведомления' },
            { icon: FiVideo, title: 'Онлайн-уроки', desc: 'Интерактивная доска, видеочат, демонстрация экрана' },
            { icon: FiBarChart2, title: 'Статистика учеников', desc: 'Отслеживайте прогресс, анализируйте успеваемость' },
            { icon: FiUsers, title: 'Группы учеников', desc: 'Объединяйте учеников в группы, создавайте общие задания' },
            { icon: FiTrendingUp, title: 'Рост и масштабирование', desc: 'От 5 до 500+ учеников — платформа растёт вместе с вами' },
          ].map((item, idx) => (
            <div key={idx} className={`bg-dark-card rounded-xl p-6 border border-white/10 hover:border-accent transition-all duration-300 hover:-translate-y-1 ${visibleSections.features ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: `${idx * 0.1}s` }}>
              <item.icon className="text-accent mb-4" size={32} />
              <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
              <p className="text-gray-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Как это работает */}
      <section id="steps" ref={stepsRef} data-section="steps" className="bg-dark-card/50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-white text-center mb-12">Как это работает</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {steps.map((step, idx) => (
              <div key={idx} className={`text-center ${visibleSections.steps ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: `${idx * 0.15}s` }}>
                <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-accent">
                  {step.number}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-gray-400 text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Отзывы */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">Что говорят репетиторы</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, idx) => (
            <div key={idx} className="bg-dark-card rounded-xl p-6 border border-white/10 hover:border-accent transition-all duration-300">
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <FiStar key={i} className="text-yellow-400 fill-yellow-400" size={16} />
                ))}
              </div>
              <p className="text-gray-300 mb-4">"{testimonial.text}"</p>
              <div className="mt-4">
                <p className="text-white font-medium">{testimonial.name}</p>
                <p className="text-gray-500 text-sm">{testimonial.role}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Для кого */}
      <section className="bg-dark-card/50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-white text-center mb-12">Кому подходит платформа</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: FiUsers, title: 'Частным репетиторам', desc: 'Всё для работы с учениками в одном месте' },
              { icon: FiBook, title: 'Репетиторским центрам', desc: 'Управление несколькими учителями и общей базой учеников' },
              { icon: FiCheckCircle, title: 'Ученикам и родителям', desc: 'Прозрачный прогресс, удобная отправка решений' },
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="w-20 h-20 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4">
                  <item.icon className="text-accent" size={32} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Тарифы */}
      <section id="pricing" ref={pricingRef} data-section="pricing" className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">Простые и понятные тарифы</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { name: 'Бесплатный', price: '0 ₽', features: ['5 учеников', '10 заданий/мес', 'Чат'], popular: false, buttonVariant: 'outline' },
            { name: 'Стандарт', price: '500 ₽', features: ['20 учеников', 'Безлимит заданий', 'Чат', 'Онлайн-уроки до 30 мин'], popular: true, buttonVariant: 'solid' },
            { name: 'Про', price: '1 000 ₽', features: ['Безлимит учеников', 'Безлимит заданий', 'Чат', 'Онлайн-уроки до 2 ч', 'Запись уроков'], popular: false, buttonVariant: 'outline' },
            { name: 'Школа', price: '3 000 ₽', features: ['До 5 учителей', 'Общая база учеников', 'Отчёты и аналитика', 'Приоритетная поддержка'], popular: false, buttonVariant: 'outline' },
          ].map((plan, idx) => (
            <div key={idx} className={`bg-dark-card rounded-xl p-6 border text-center transition-all duration-300 hover:-translate-y-1 ${plan.popular ? 'border-accent relative' : 'border-white/10'} ${visibleSections.pricing ? 'animate-fade-in-up' : 'opacity-0'}`} style={{ animationDelay: `${idx * 0.1}s` }}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-accent text-white text-xs px-3 py-1 rounded-full">
                  Популярный
                </div>
              )}
              <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
              <div className="text-3xl font-bold text-accent mb-4">{plan.price}</div>
              <ul className="text-gray-400 text-sm space-y-2 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i}>{feature}</li>
                ))}
              </ul>
              <Link to="/register" className={`block w-full py-2 rounded-lg transition ${plan.popular ? 'bg-accent hover:bg-accent/80 text-white' : 'border border-white/20 text-white hover:bg-white/10'}`}>
                Выбрать
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">Часто задаваемые вопросы</h2>
        <div className="max-w-3xl mx-auto space-y-4">
          {faqItems.map((item, idx) => (
            <div key={idx} className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-white/5 transition"
              >
                <span className="text-white font-medium">{item.question}</span>
                <FiChevronRight className={`text-gray-400 transition-transform duration-300 ${activeFaq === idx ? 'rotate-90' : ''}`} />
              </button>
              <div className={`px-6 overflow-hidden transition-all duration-300 ${activeFaq === idx ? 'py-4 border-t border-white/10' : 'max-h-0'}`}>
                <p className="text-gray-400">{item.answer}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Призыв к действию */}
      <section className="bg-gradient-to-r from-accent/20 to-accent/10 py-16 text-center">
        <div className="container mx-auto px-4">
          <h2 className="text-2xl font-bold text-white mb-4">Готовы начать?</h2>
          <p className="text-gray-400 mb-6">Присоединяйтесь к сообществу репетиторов уже сегодня</p>
          <Link to="/register" className="px-8 py-3 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium inline-flex items-center gap-2 transition">
            Начать бесплатно <FiArrowRight />
          </Link>
          <p className="text-gray-500 text-sm mt-4">Не требуется кредитная карта</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-dark-card border-t border-white/10 py-8">
        <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
          <p>© 2026 Math Tutor Platform. Все права защищены.</p>
          <div className="flex justify-center gap-4 mt-2">
            <Link to="/privacy" className="hover:text-accent transition">Политика конфиденциальности</Link>
            <Link to="/contacts" className="hover:text-accent transition">Контакты</Link>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease forwards;
        }
      `}</style>
    </div>
  );
};

export default LandingPage;