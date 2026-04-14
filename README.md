# Math Tutor Platform

Образовательная платформа для репетиторов и учеников.  
Позволяет создавать задания, отправлять решения, общаться в чате в реальном времени.

## 🌐 Демо

- Сайт: [https://tutor-platform.ru](https://tutor-platform.ru)
- API документация: [https://tutor-platform.ru/docs](https://tutor-platform.ru/docs) (доступ по логину/паролю)

## 🛠 Стек технологий

### Backend
- Python 3.11, FastAPI
- PostgreSQL, SQLAlchemy (async)
- JWT, HttpOnly cookies
- WebSocket (Socket.IO)
- Docker, Nginx

### Frontend
- React 18, TypeScript
- TailwindCSS
- Vite
- React Router, React Query

### DevOps
- Linux (Ubuntu), VPS (Beget)
- Nginx, SSL (Let's Encrypt)
- systemd, Git

## 🚀 Функционал

- 👨‍🏫 **Учитель**: создание/редактирование/удаление заданий, проверка решений, фидбек
- 🧑‍🎓 **Ученик**: просмотр заданий, отправка решений (текст + файлы), просмотр фидбека
- 💬 **Чат в реальном времени** (WebSocket)
- 📎 **Загрузка файлов** (изображения, PDF, документы)
- 🌙 **Тёмная и светлая тема**
- 🔐 **Безопасность**: JWT в HttpOnly cookies, rate limiting, security-заголовки

## 📦 Установка и запуск

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Переменные окружения

Создай файл .env в папке backend:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://localhost:5173
```

### 🐳 Docker

```bash
docker-compose up -d
```

### Лицензия 

MIT

### 👤 Автор

Мирхабибов Бохиржон — [GitHub](https://github.com/H4R4K1RI)
