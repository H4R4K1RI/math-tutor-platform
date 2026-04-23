import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Footer from './components/Footer';
import AnimatedPage from './components/AnimatedPage';
import { initSocket } from './socket';
import Privacy from './pages/Privacy';
import Contacts from './pages/Contacts';

// Ленивая загрузка страниц
const Login = lazy(() => import('./pages/Login').then(module => ({ default: module.default })));
const Register = lazy(() => import('./pages/Register').then(module => ({ default: module.default })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.default })));
const Assignments = lazy(() => import('./pages/Assignments').then(module => ({ default: module.default })));
const AssignmentDetail = lazy(() => import('./pages/AssignmentDetail').then(module => ({ default: module.default })));
const ReviewSubmissions = lazy(() => import('./pages/ReviewSubmissions').then(module => ({ default: module.default })));
const Chats = lazy(() => import('./pages/Chats').then(module => ({ default: module.default })));
const ChatRoom = lazy(() => import('./pages/ChatRoom').then(module => ({ default: module.default })));

const LazyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<div className="text-center py-20 text-white">Загрузка...</div>}>
    {children}
  </Suspense>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="text-center py-20 text-white">Загрузка...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
};

const TeacherRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isTeacher, isLoading } = useAuth();
  if (isLoading) return <div className="text-center py-20 text-white">Загрузка...</div>;
  if (!user) return <Navigate to="/login" />;
  if (!isTeacher) return <Navigate to="/dashboard" />;
  return <>{children}</>;
};

function AppRoutes() {
  const location = useLocation();
  const { user, isLoading } = useAuth();

  if (isLoading) return <div className="text-center py-20 text-white">Загрузка приложения...</div>;

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
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
        <Route path="/privacy" element={<LazyRoute><Privacy /></LazyRoute>} />
        <Route path="/contacts" element={<LazyRoute><Contacts /></LazyRoute>} />
        <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} />} />
      </Routes>
    </AnimatePresence>
  );
}

function AppContent() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const isChatPage = location.pathname.startsWith('/chat/');
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    initSocket();
  }, []);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col">
      {!isChatPage && (
        <Header 
          darkMode={darkMode} 
          setDarkMode={setDarkMode} 
          onMenuClick={() => setSidebarOpen(true)} 
        />
      )}
      
      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <main className={`flex-1 transition-all duration-300 ${sidebarOpen && !isAuthPage && !isChatPage ? 'ml-72' : ''}`}>
        <div className={`${isChatPage ? 'p-0' : 'p-6'}`}>
          <AppRoutes />
        </div>
      </main>
      
      {!isChatPage && <Footer />}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
