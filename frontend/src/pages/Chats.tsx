import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { socket } from '../socket';
import { FiMessageCircle } from 'react-icons/fi';

interface Chat {
  id: number;
  other_user_id: number;
  other_user_name: string;
  assignment_id: number | null;
  last_message: string | null;
  last_message_time: string | null;
  unread_count: number;
}

const Chats: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    fetchChats();
    
    socket.on('new_message', () => {
      fetchChats();
    });
    
    return () => {
      socket.off('new_message');
    };
  }, []);

  if (loading) return <div className="text-center py-20">Загрузка...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Сообщения</h1>
      
      {chats.length === 0 ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400">
          <FiMessageCircle size={48} className="mx-auto mb-4 opacity-50" />
          <p>У вас пока нет чатов</p>
          <p className="text-sm">Начните общение с учеником из проверки решений</p>
        </div>
      ) : (
        <div className="space-y-2">
          {chats.map(chat => (
            <Link
              key={chat.id}
              to={`/chat/${chat.id}`}
              className="block bg-white dark:bg-[#1a1a1a] rounded-lg shadow hover:shadow-md transition p-4 border border-gray-200 dark:border-gray-700"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg dark:text-white">
                    {chat.other_user_name}
                    {chat.assignment_id && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                        (Задание #{chat.assignment_id})
                      </span>
                    )}
                  </h3>
                  {chat.last_message && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm mt-1 line-clamp-1">
                      {chat.last_message}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  {chat.last_message_time && (
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {new Date(chat.last_message_time).toLocaleDateString()}
                    </p>
                  )}
                  {chat.unread_count > 0 && (
                    <span className="inline-block mt-1 bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                      {chat.unread_count}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default Chats;