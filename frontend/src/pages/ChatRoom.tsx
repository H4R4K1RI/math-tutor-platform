import React, { useEffect, useState, useRef, lazy, Suspense } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { socket } from '../socket';
import { useAuth } from '../context/AuthContext';
import { FiSend, FiSmile, FiArrowLeft, FiEdit2, FiTrash2 } from 'react-icons/fi';
import toast from 'react-hot-toast';
import AnimatedPage from '../components/AnimatedPage';

const EmojiPicker = lazy(() => import('emoji-picker-react'));

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
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [isUserTyping, setIsUserTyping] = useState(false);
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоадаптация под адресную строку браузера
  useEffect(() => {
    const handleResize = () => {
      setViewportHeight(window.innerHeight);
    };
    
    window.addEventListener('resize', handleResize);
    
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          setViewportHeight(window.innerHeight);
          ticking = false;
        });
        ticking = true;
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('orientationchange', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  // Инициализация чата (остальное без изменений)
  useEffect(() => {
    const initChat = async () => {
      try {
        if (assignmentId) {
          const response = await apiClient.get(`/chats/assignment/${assignmentId}`);
          const newChatId = response.data.chat_id;
          navigate(`/chat/${newChatId}`, { replace: true });
          return;
        }
        if (studentId) {
          const response = await apiClient.get(`/chats/student/${studentId}`);
          const newChatId = response.data.chat_id;
          navigate(`/chat/${newChatId}`, { replace: true });
          return;
<div className="flex-1">
      <h2 className="text-xl font-semibold text-white">{otherUserName || 'Чат'}</h2>
      {isUserTyping && (
        <p className="text-xs text-accent animate-pulse">печатает...</p>
      )}
    </div>        }
        if (id) setChatId(parseInt(id));
      } catch (error) {
        console.error('Error initializing chat:', error);
        toast.error('Ошибка при загрузке чата');
        navigate('/chats');
      }
    };
    initChat();
  }, [id, studentId, assignmentId, navigate]);

  // Загрузка сообщений
  const fetchMessages = async () => {
    if (!chatId) return;
    try {
      const response = await apiClient.get(`/chats/${chatId}/messages`);
      setMessages(response.data);
      if (socket?.connected) {
        socket.emit('mark_messages_read', { chat_id: chatId, user_id: user?.id });
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Ошибка при загрузке сообщений');
      navigate('/chats');
    } finally {
      setLoading(false);
    }
  };

  // Информация о чате
  const fetchChatInfo = async () => {
    if (!chatId) return;
    try {
      const response = await apiClient.get('/chats');
      const chat = response.data.find((c: any) => c.id === chatId);
      if (chat) setOtherUserName(chat.other_user_name);
    } catch (error) {
      console.error('Error fetching chat info:', error);
    }
  };

  // Подключение к WebSocket
  useEffect(() => {
    if (!chatId || !socket) return;

    if (socket.connected) {
      socket.emit('join_chat', { chat_id: chatId });
    } else {
      socket.once('connect', () => {
        socket?.emit('join_chat', { chat_id: chatId });
      });
    }

    const handleNewMessage = (data: any) => {
      if (data.chat_id === chatId) {
        setMessages(prev => [...prev, data]);
        if (data.sender_id !== user?.id && socket?.connected) {
          socket?.emit('mark_messages_read', { chat_id: chatId, user_id: user?.id });
        }
      }
    };

    const handleChatCleared = (data: any) => {
      if (data.chat_id === chatId) {
        setMessages([]);
        toast.success('История чата очищена');
      }
    };

    const handleChatDeleted = (data: any) => {
      if (data.chat_id === chatId) {
        toast.success('Чат удалён');
        navigate('/chats');
      }
    };

    const handleMessageEdited = (data: any) => {
      if (data.chat_id === chatId) {
        setMessages(prev => prev.map(msg => 
          msg.id === data.message_id ? { ...msg, message: data.new_message } : msg
        ));
      }
    };

    const handleMessageDeleted = (data: any) => {
      if (data.chat_id === chatId) {
        setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
      }
    };

    const handleUserTyping = (data: any) => {
      if (data.chat_id === chatId && data.user_id !== user?.id) {
        setIsUserTyping(data.is_typing);
        if (data.is_typing) {
          setTimeout(() => setIsUserTyping(false), 3000);
        }
      }
    };

    socket.on('new_message', handleNewMessage);
    socket.on('chat_cleared', handleChatCleared);
    socket.on('chat_deleted', handleChatDeleted);
    socket.on('message_edited', handleMessageEdited);
    socket.on('message_deleted', handleMessageDeleted);
    socket.on('user_typing', handleUserTyping);

    fetchMessages();
    fetchChatInfo();

    return () => {
      if (socket) {socket.off('new_message', handleNewMessage);
      socket.off('chat_cleared', handleChatCleared);
      socket.off('chat_deleted', handleChatDeleted);
      socket.off('message_edited', handleMessageEdited);
      socket.off('message_deleted', handleMessageDeleted);
      socket.off('user_typing', handleUserTyping);}
    };
  }, [chatId, user?.id, navigate, socket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !chatId || !user?.id) return;
    
    if (!socket?.connected) {
      toast.error('Нет соединения с сервером');
      return;
    }
    
    socket.emit('send_message', { 
      chat_id: chatId, 
      sender_id: user.id, 
      message: newMessage.trim()
    });
    setNewMessage('');
  };

  const handleTyping = () => {
    if (!socket?.connected || !chatId) return;
    
    socket.emit('typing_start', { chat_id: chatId });
    
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    
    typingTimeoutRef.current = setTimeout(() => {
      socket?.emit('typing_stop', { chat_id: chatId });
    }, 1000);
  };

  const handleClearHistory = async () => {
    if (!chatId || !confirm('Очистить всю историю сообщений? Это действие нельзя отменить.')) return;
    try {
      await apiClient.delete(`/chats/${chatId}/messages`);
      setMessages([]);
      toast.success('История очищена');
    } catch (error) {
      console.error(error);
      toast.error('Ошибка при очистке');
    }
  };

  const handleDeleteChat = async () => {
    if (!chatId || !confirm('Удалить чат навсегда? Это действие нельзя отменить.')) return;
    try {
      await apiClient.delete(`/chats/${chatId}`);
      navigate('/chats');
      toast.success('Чат удалён');
    } catch (error) {
      console.error(error);
      toast.error('Ошибка при удалении');
    }
  };

  const handleEditMessage = async (messageId: number, newText: string) => {
    if (!newText.trim()) return;
    try {
      await apiClient.put(`/chats/messages/${messageId}`, null, { 
        params: { new_message: newText.trim() } 
      });
      setEditingMessageId(null);
      setEditText('');
      toast.success('Сообщение отредактировано');
    } catch (error) {
      console.error(error);
      toast.error('Ошибка при редактировании');
    }
  };

  const handleDeleteMessage = async (messageId: number) => {
    if (!confirm('Удалить сообщение?')) return;
    try {
      await apiClient.delete(`/chats/messages/${messageId}`);
      toast.success('Сообщение удалено');
    } catch (error) {
      console.error(error);
      toast.error('Ошибка при удалении');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center bg-dark-bg" style={{ height: viewportHeight }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-white">Загрузка чата...</p>
        </div>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="flex flex-col bg-dark-bg" style={{ height: viewportHeight }}>
        {/* Header чата */}
        <div className="bg-dark-card shadow p-4 border-b border-white/10 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate('/chats')} 
              className="p-1 rounded-lg hover:bg-white/10 transition" 
              aria-label="Назад к чатам"
            >
              <FiArrowLeft size={24} className="text-gray-300" />
            </button>

            <div className="flex items-center gap-2 flex-1 flex-wrap">
              <h2 className="text-xl font-semibold text-white">{otherUserName || 'Чат'}</h2>
              {isUserTyping && (
                <span className="text-sm text-accent animate-pulse font-medium">печатает...</span>
              )}
            </div>

          </div>
          <div className="flex gap-3 mt-3">
            <button 
              onClick={handleClearHistory} 
              className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-red-600 text-gray-300 hover:text-white transition-all duration-200 text-sm font-medium"
            >
              🗑️ Очистить
            </button>
            <button 
              onClick={handleDeleteChat} 
              className="px-3 py-1 rounded-lg bg-gray-700 hover:bg-red-600 text-gray-300 hover:text-white transition-all duration-200 text-sm font-medium"
            >
              ❌ Удалить чат
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 pt-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-10">Напишите первое сообщение</div>
          ) : (
            <>
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[70%] rounded-lg px-4 py-2 shadow ${
                    msg.sender_id === user?.id
                      ? 'bg-accent text-white'
                      : 'bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-200'
                  }`}>
                    {editingMessageId === msg.id ? (
                      <div className="flex flex-col gap-2">
                        <input 
                          type="text" 
                          value={editText} 
                          onChange={(e) => setEditText(e.target.value)} 
                          className="w-full px-2 py-1 border rounded bg-gray-700 text-white" 
                          autoFocus 
                        />
                        <div className="flex gap-2 justify-end">
                          <button 
                            onClick={() => handleEditMessage(msg.id, editText)} 
                            className="bg-green-700 hover:bg-green-600 text-white px-2 py-1 rounded text-sm"
                          >
                            💾 Сохранить
                          </button>
                          <button 
                            onClick={() => setEditingMessageId(null)} 
                            className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm"
                          >
                            ✖ Отмена
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="break-words whitespace-pre-wrap">{msg.message}</p>
                        <p className={`text-xs mt-1 ${
                          msg.sender_id === user?.id ? 'text-white/70' : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                        {msg.sender_id === user?.id && (
                          <div className="flex gap-2 justify-end mt-1">
                            <button 
                              onClick={() => { setEditingMessageId(msg.id); setEditText(msg.message); }} 
                              className="text-gray-400 hover:text-accent transition" title="Редактировать"
                            >
                              <FiEdit2 size={14} />
                            </button>
                            <button 
                              onClick={() => handleDeleteMessage(msg.id)} 
                              className="text-gray-400 hover:text-danger transition" title="Удалить"
                            >
                              <FiTrash2 size={14} />
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={sendMessage} className="border-t border-white/10 flex gap-2 relative flex-shrink-0 bg-dark-card px-4 py-3">
          <button 
            type="button" 
            onClick={() => setShowEmojiPicker(!showEmojiPicker)} 
            className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg transition" title="Выбрать эмодзи"
          >
            <FiSmile size={20} />
          </button>
          <input 
            type="text" 
            value={newMessage} 
            onChange={(e) => { setNewMessage(e.target.value); handleTyping(); }} 
            placeholder="Введите сообщение..." 
            className="flex-1 px-4 py-2 border border-gray-700 rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent bg-gray-800 text-white"
          />
          <button 
            type="submit" 
            className="bg-accent hover:bg-accent/80 text-white px-4 py-2 rounded-lg transition" title="Отправить"
          >
            <FiSend size={20} />
          </button>
          
          {showEmojiPicker && (
            <div className="absolute bottom-full right-0 mb-2 z-50">
              <Suspense fallback={<div className="p-2 text-center bg-gray-800 rounded">Загрузка...</div>}>
                <EmojiPicker onEmojiClick={(emoji) => { setNewMessage(prev => prev + emoji.emoji); setShowEmojiPicker(false); }} />
              </Suspense>
            </div>
          )}
        </form>
      </div>
    </AnimatedPage>
  );
};

export default ChatRoom;
