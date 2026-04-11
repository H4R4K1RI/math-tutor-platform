import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Assignments from './pages/Assignments';
import AssignmentDetail from './pages/AssignmentDetail';
import ReviewSubmissions from './pages/ReviewSubmissions';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
};

const TeacherRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isTeacher } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (!isTeacher) return <Navigate to="/dashboard" />;
  return <>{children}</>;
};

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/assignments" element={<TeacherRoute><Assignments /></TeacherRoute>} />
        <Route path="/assignment/:id" element={<ProtectedRoute><AssignmentDetail /></ProtectedRoute>} />
        <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} />} />
        <Route path="/review" element={<TeacherRoute><ReviewSubmissions /></TeacherRoute>} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;