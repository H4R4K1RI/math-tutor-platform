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
import GlobalNotification from './components/GlobalNotification';
import { ChatProvider } from './context/ChatContext';
import StudentsPage from './pages/StudentsPage';
import StudentStatsPage from './pages/StudentStatsPage';
import GroupsPage from './pages/GroupsPage';
import GroupDetailPage from './pages/GroupDetailPage';
import ProfilePage from './pages/ProfilePage';
import TutorPage from './pages/TutorPage';
import LandingPage from './pages/LandingPage';
import TestsPage from './pages/TestsPage';
import TestEditorPage from './pages/TestEditorPage';
import TakeTestPage from './pages/TakeTestPage';
import TestResultPage from './pages/TestResultPage';
import TestResultsTeacherPage from './pages/TestResultsTeacherPage';
import MyTestsPage from './pages/MyTestsPage';
import TestStudentResultPage from './pages/TestStudentResultPage';
import VerifyEmail from './pages/VerifyEmail';
import FinancePage from './pages/FinancePage';
import PaymentHistory from './pages/PaymentHistory';
import CalendarPage from './pages/CalendarPage';
import LessonRequestsPage from './pages/LessonRequestsPage';
import MaterialsPage from './pages/MaterialsPage';
import TutoringRequestsPage from './pages/TutoringRequestsPage';
import JoinByInvite from './pages/JoinByInvite';
import LessonPage from './pages/LessonPage';
import { Toaster } from 'react-hot-toast';

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
        <Route path="/students" element={<TeacherRoute><LazyRoute><StudentsPage /></LazyRoute></TeacherRoute>} />
        <Route path="/students/:id" element={<TeacherRoute><LazyRoute><StudentStatsPage /></LazyRoute></TeacherRoute>} />
        <Route path="/groups" element={<TeacherRoute><LazyRoute><GroupsPage /></LazyRoute></TeacherRoute>} />
        <Route path="/groups/:id" element={<TeacherRoute><LazyRoute><GroupDetailPage /></LazyRoute></TeacherRoute>} />
        <Route path="/profile" element={<ProtectedRoute><LazyRoute><ProfilePage /></LazyRoute></ProtectedRoute>} />
        <Route path="/tutor/:id" element={<LazyRoute><TutorPage /></LazyRoute>} />
        <Route path="/tests" element={<TeacherRoute><LazyRoute><TestsPage /></LazyRoute></TeacherRoute>} />
        <Route path="/tests/new" element={<TeacherRoute><LazyRoute><TestEditorPage /></LazyRoute></TeacherRoute>} />
        <Route path="/tests/:id/edit" element={<TeacherRoute><LazyRoute><TestEditorPage /></LazyRoute></TeacherRoute>} />
        <Route path="/my-tests" element={<ProtectedRoute><LazyRoute><MyTestsPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/test/:id" element={<LazyRoute><TakeTestPage /></LazyRoute>} />
        <Route path="/test/:id/result" element={<LazyRoute><TestResultPage /></LazyRoute>} />
        <Route path="/tests/:id/results" element={<TeacherRoute><LazyRoute><TestResultsTeacherPage /></LazyRoute></TeacherRoute>} />
        <Route path="/tests/:testId/results/:userId" element={<TeacherRoute><LazyRoute><TestStudentResultPage /></LazyRoute></TeacherRoute>} />
        <Route path="/verify-email" element={<LazyRoute><VerifyEmail /></LazyRoute>} />
        <Route path="/finance" element={<TeacherRoute><LazyRoute><FinancePage /></LazyRoute></TeacherRoute>} />
        <Route path="/payments" element={<ProtectedRoute><LazyRoute><PaymentHistory /></LazyRoute></ProtectedRoute>} />
        <Route path="/calendar" element={<ProtectedRoute><LazyRoute><CalendarPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/lesson/:id" element={<ProtectedRoute><LazyRoute><LessonPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/requests" element={<ProtectedRoute><LazyRoute><LessonRequestsPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/materials" element={<ProtectedRoute><LazyRoute><MaterialsPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/tutoring-requests" element={<ProtectedRoute><LazyRoute><TutoringRequestsPage /></LazyRoute></ProtectedRoute>} />
        <Route path="/join" element={<LazyRoute><JoinByInvite /></LazyRoute>} />
      </Routes>
    </AnimatePresence>
  );
}

function AppContent() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const isFullscreenPage =
  location.pathname.startsWith('/chat/') ||
  location.pathname.startsWith('/lesson/');
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
      {!isFullscreenPage && (
        <Header
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          onMenuClick={() => setSidebarOpen(true)}
        />
      )}

      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className={`flex-1 transition-all duration-300 ${sidebarOpen && !isAuthPage && !isFullscreenPage ? 'ml-72' : ''}`}>
        <div className={`${isFullscreenPage ? 'p-0' : 'p-6'}`}>
          <AppRoutes />
        </div>
      </main>

      {!isFullscreenPage && <Footer />}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/*" element={
          <AuthProvider>
            <ChatProvider>
              <GlobalNotification />
              <AppContent />
              <Toaster position="top-right" />
            </ChatProvider>
          </AuthProvider>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;