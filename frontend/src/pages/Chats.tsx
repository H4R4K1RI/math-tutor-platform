import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { socket } from '../socket';
import { useAuth } from '../context/AuthContext';
import { FiMessageCircle, FiPlus } from 'react-icons/fi';
import AnimatedPage from '../components/AnimatedPage';

interface Chat {
  id: number;
  other_user_id: number;
  other_user_name: string;
  assignment_id: number | null;
  last_message: string | null;
  last_message_time: string | null;
  unread_count: number;
}

interface Student {
  id: number;
  full_name: string;
  email: string;
}

const Chats: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [chats, setChats] = useState<Chat[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const fetchChats = async () => {
    try {
      const response = await apiClient.get('/chats');
      setChats(response.data);
    } catch (error) {
      console.error('Error fetching chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/users/students');
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  useEffect(() => {
    fetchChats();
    if (isTeacher) fetchStudents();
    
    socket.on('new_message', () => fetchChats());
    socket.on('chat_deleted', () => fetchChats());
    socket.on('chat_cleared', () => fetchChats());
    
    return () => {
      socket.off('new_message');
      socket.off('chat_deleted');
      socket.off('chat_cleared');
    };
  }, [isTeacher]);

  const createChat = async () => {
    if (!selectedStudent) return;
    setCreating(true);
    try {
      const response = await apiClient.post('/chats/', { student_id: Number(selectedStudent), assignment_id: null });
      window.location.href = `/chat/${response.data.chat_id}`;
    } catch (error) {
      console.error('Error creating chat:', error);
      alert('Ошибка при создании чата');
    } finally {
      setCreating(false);
      setShowModal(false);
      setSelectedStudent(null);
    }
  };

  if (loading) return <div className="text-center py-20 text-white">Загрузка...</div>;

  return (
    <AnimatedPage>
      <div className="max-w-4xl mx-auto relative min-h-[calc(100vh-120px)]">
        <h1 className="text-2xl font-bold mb-6 text-white">Сообщения</h1>
        
        {chats.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiMessageCircle size={48} className="mx-auto mb-4 opacity-50" />
            <p>У вас пока нет чатов</p>
            {isTeacher && <p className="text-sm">Нажмите на кнопку ➕ в правом нижнем углу, чтобы начать общение</p>}
          </div>
        ) : (
          <div className="space-y-2">
            {chats.map(chat => (
              <Link key={chat.id} to={`/chat/${chat.id}`} className="block bg-dark-card rounded-lg shadow hover:shadow-md transition p-4 border border-white/10">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-white">{chat.other_user_name}</h3>
                    {chat.last_message && <p className="text-gray-400 text-sm mt-1 line-clamp-1">{chat.last_message}</p>}
                  </div>
                  <div className="text-right">
                    {chat.last_message_time && <p className="text-xs text-gray-500">{new Date(chat.last_message_time).toLocaleDateString()}</p>}
                    {chat.unread_count > 0 && <span className="inline-block mt-1 bg-red-500 text-white text-xs rounded-full px-2 py-0.5">{chat.unread_count}</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {isTeacher && (
          <button onClick={() => setShowModal(true)} className="fixed bottom-6 right-6 bg-accent hover:bg-accent/80 text-white p-4 rounded-full shadow-lg transition-all duration-200 hover:scale-105 z-50">
            <FiPlus size={24} />
          </button>
        )}

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-lg shadow-xl p-6 w-full max-w-md border border-white/10">
              <h2 className="text-xl font-semibold mb-4 text-white">Выберите ученика</h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {students.map(student => (
                  <button key={student.id} onClick={() => setSelectedStudent(student.id)} className={`w-full text-left p-3 rounded-lg transition ${selectedStudent === student.id ? 'bg-accent text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'}`}>
                    <p className="font-medium">{student.full_name}</p>
                    <p className="text-sm opacity-75">{student.email}</p>
                  </button>
                ))}
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button onClick={() => setShowModal(false)} className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition">Отмена</button>
                <button onClick={createChat} disabled={!selectedStudent || creating} className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white font-semibold disabled:opacity-50 transition">Начать чат</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default Chats;
