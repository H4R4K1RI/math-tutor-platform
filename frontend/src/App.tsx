import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import { FiMenu } from 'react-icons/fi';

// Ленивая загрузка страниц
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Assignments = lazy(() => import('./pages/Assignments'));
const AssignmentDetail = lazy(() => import('./pages/AssignmentDetail'));
const ReviewSubmissions = lazy(() => import('./pages/ReviewSubmissions'));
const Chats = lazy(() => import('./pages/Chats'));
const ChatRoom = lazy(() => import('./pages/ChatRoom'));

const LazyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<div className="text-center py-20">Загрузка...</div>}>
    {children}
  </Suspense>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="text-center py-20">Загрузка...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
};

const TeacherRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isTeacher, isLoading } = useAuth();
  if (isLoading) return <div className="text-center py-20">Загрузка...</div>;
  if (!user) return <Navigate to="/login" />;
  if (!isTeacher) return <Navigate to="/dashboard" />;
  return <>{children}</>;
};

function AppRoutes() {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  if (isLoading) {
    return <div className="text-center py-20">Загрузка приложения...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<LazyRoute><Login /></LazyRoute>} />
      <Route path="/register" element={<LazyRoute><Register /></LazyRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><LazyRoute><Dashboard /></LazyRoute></ProtectedRoute>} />
      <Route path="/assignments" element={<TeacherRoute><LazyRoute><Assignments /></LazyRoute></TeacherRoute>} />
      <Route path="/assignment/:id" element={<ProtectedRoute><LazyRoute><AssignmentDetail /></LazyRoute></ProtectedRoute>} />
      <Route path="/review" element={<TeacherRoute><LazyRoute><ReviewSubmissions /></LazyRoute></TeacherRoute>} />
      <Route path="/chats" element={<ProtectedRoute><LazyRoute><Chats /></LazyRoute></ProtectedRoute>} />
      <Route path="/chat/:id" element={<ProtectedRoute><LazyRoute><ChatRoom /></LazyRoute></ProtectedRoute>} />
      <Route path="/chat/student/:studentId" element={<ProtectedRoute><LazyRoute><ChatRoom /></LazyRoute></ProtectedRoute>} />
      <Route path="/chat/assignment/:assignmentId" element={<ProtectedRoute><LazyRoute><ChatRoom /></LazyRoute></ProtectedRoute>} />
      <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} />} />
    </Routes>
  );
}

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved === 'true';
  });
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="fixed top-4 left-4 z-50 p-2 rounded-lg border border-[#2e7d5e] text-[#2e7d5e] hover:bg-[#2e7d5e] hover:text-white bg-white dark:bg-[#0d1b12] transition-all duration-200 shadow-md"
            aria-label="Toggle sidebar"
          >
            <FiMenu size={24} />
          </button>

          <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

          <main className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-64' : 'lg:ml-0'}`}>
            <AppRoutes />
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;