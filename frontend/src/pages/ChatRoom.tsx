import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { socket } from '../socket';
import { useAuth } from '../context/AuthContext';
import { FiSend, FiSmile } from 'react-icons/fi';
import EmojiPicker from 'emoji-picker-react';

interface Message {
  id: number;
  chat_id: number;
  sender_id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

const ChatRoom: React.FC = () => {
  const { id, studentId, assignmentId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [otherUserName, setOtherUserName] = useState('');
  const [chatId, setChatId] = useState<number | null>(null);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Инициализация чата
  useEffect(() => {
    const initChat = async () => {
      try {
        if (assignmentId) {
          const response = await apiClient.get(`/chats/assignment/${assignmentId}`);
          setChatId(response.data.chat_id);
          navigate(`/chat/${response.data.chat_id}`, { replace: true });
          return;
        }
        if (studentId) {
          const response = await apiClient.get(`/chats/student/${studentId}`);
          setChatId(response.data.chat_id);
          navigate(`/chat/${response.data.chat_id}`, { replace: true });
          return;
        }
        if (id) {
          setChatId(parseInt(id));
        }
      } catch (error) {
        console.error('Error initializing chat:', error);
        navigate('/chats');
      }
    };
    
    initChat();
  }, [id, studentId, assignmentId, navigate]);

  const fetchMessages = async () => {
    if (!chatId) return;
    try {
      const response = await apiClient.get(`/chats/${chatId}/messages`);
      setMessages(response.data);
      socket.emit('mark_messages_read', { chat_id: chatId, user_id: user?.id });
    } catch (error) {
      console.error('Error fetching messages:', error);
      navigate('/chats');
    } finally {
      setLoading(false);
    }
  };

  const fetchChatInfo = async () => {
    if (!chatId) return;
    try {
      const response = await apiClient.get('/chats');
      const chat = response.data.find((c: any) => c.id === chatId);
      if (chat) {
        setOtherUserName(chat.other_user_name);
      }
    } catch (error) {
      console.error('Error fetching chat info:', error);
    }
  };

  useEffect(() => {
    if (chatId) {
      fetchMessages();
      fetchChatInfo();
      
      socket.emit('join_chat', { chat_id: chatId });
      
      socket.on('new_message', (data: any) => {
        if (data.chat_id === chatId) {
          setMessages(prev => [...prev, data]);
          if (data.sender_id !== user?.id) {
            socket.emit('mark_messages_read', { chat_id: chatId, user_id: user?.id });
          }
        }
      });
      
      return () => {
        socket.off('new_message');
      };
    }
  }, [chatId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !chatId) return;
    
    socket.emit('send_message', {
      chat_id: chatId,
      sender_id: user?.id,
      message: newMessage.trim()
    });
    
    setNewMessage('');
  };

  if (loading) return <div className="text-center py-20">Загрузка...</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <div className="bg-white dark:bg-[#1a1a1a] rounded-t-lg shadow p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold dark:text-white">{otherUserName || 'Чат'}</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-[#121212] rounded-b-lg">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-10">
            Напишите первое сообщение
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 shadow ${
                  msg.sender_id === user?.id
                    ? '!bg-green-100 dark:!bg-green-800 text-gray-900 dark:text-white'
                    : '!bg-gray-100 dark:!bg-gray-700 text-gray-900 dark:text-white'
                }`}
              >
                <p className="break-words">{msg.message}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={sendMessage} className="mt-4 flex gap-2 relative">
        <button
          type="button"
          onClick={() => setShowEmojiPicker(!showEmojiPicker)}
          className="bg-gray-200 dark:bg-[#2a2a2a] hover:bg-gray-300 dark:hover:bg-[#3a3a3a] text-gray-700 dark:text-gray-300 px-3 py-2 rounded-lg transition"
        >
          <FiSmile size={20} />
        </button>
        
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Введите сообщение..."
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#2e7d5e] focus:border-transparent bg-white dark:bg-[#2a2a2a] text-gray-900 dark:text-white"
        />
        
        <button
          type="submit"
          className="bg-[#2e7d5e] hover:bg-[#1e5a44] text-white px-4 py-2 rounded-lg transition"
        >
          <FiSend size={20} />
        </button>
        
        {showEmojiPicker && (
          <div className="absolute bottom-full right-0 mb-2 z-50">
            <EmojiPicker
              onEmojiClick={(emoji) => {
                setNewMessage(prev => prev + emoji.emoji);
                setShowEmojiPicker(false);
              }}
            />
          </div>
        )}
      </form>
    </div>
  );
};

export default ChatRoom;
