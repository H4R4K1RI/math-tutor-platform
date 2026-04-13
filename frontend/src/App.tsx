import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Assignments from './pages/Assignments';
import AssignmentDetail from './pages/AssignmentDetail';
import ReviewSubmissions from './pages/ReviewSubmissions';
import { FiMenu } from 'react-icons/fi';
import Chats from './pages/Chats';
import ChatRoom from './pages/ChatRoom';

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

  if (isLoading) {
    return <div className="text-center py-20">Загрузка приложения...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/assignments" element={<TeacherRoute><Assignments /></TeacherRoute>} />
      <Route path="/assignment/:id" element={<ProtectedRoute><AssignmentDetail /></ProtectedRoute>} />
      <Route path="/review" element={<TeacherRoute><ReviewSubmissions /></TeacherRoute>} />
      <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} />} />
      <Route path="/chats" element={<ProtectedRoute><Chats /></ProtectedRoute>} />
      <Route path="/chat/:id" element={<ProtectedRoute><ChatRoom /></ProtectedRoute>} />
      <Route path="/chat/student/:studentId" element={<ProtectedRoute><ChatRoom /></ProtectedRoute>} />
      <Route path="/chat/assignment/:assignmentId" element={<ProtectedRoute><ChatRoom /></ProtectedRoute>} />
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
          {/* Кнопка для мобильных и ПК */}
          <button
  onClick={() => setSidebarOpen(!sidebarOpen)}
  className="fixed top-4 left-4 z-50 p-2 rounded-lg border border-[#2e7d5e] text-[#2e7d5e] hover:bg-[#2e7d5e] hover:text-white bg-transparent transition-all duration-200 shadow-md"
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
