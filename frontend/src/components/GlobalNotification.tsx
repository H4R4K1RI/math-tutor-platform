import React, { useEffect, useRef, useState } from 'react';
import { socket } from '../socket';
import { useAuth } from '../context/AuthContext';

let audioContext: AudioContext | null = null;
let audioBuffer: AudioBuffer | null = null;
let activeChatId: number | null = null;

export const setActiveChat = (chatId: number | null) => {
  activeChatId = chatId;
};

const GlobalNotification: React.FC = () => {
  const { user } = useAuth();
  const [isSocketConnected, setIsSocketConnected] = useState(false);
  const originalTitle = useRef(document.title);

  // Загрузка звука (без изменений)
  useEffect(() => {
    const loadSound = async () => {
      try {
        const response = await fetch('/notification.mp3');
        const arrayBuffer = await response.arrayBuffer();
        audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        console.log('✅ Sound loaded');
      } catch (error) {
        console.error('Failed to load sound:', error);
      }
    };
    loadSound();

    const initAudioOnClick = () => {
      if (audioContext && audioContext.state === 'suspended') {
        audioContext.resume();
      }
      document.removeEventListener('click', initAudioOnClick);
    };
    document.addEventListener('click', initAudioOnClick);
    return () => document.removeEventListener('click', initAudioOnClick);
  }, []);

  const playSound = () => {
    if (!audioContext || !audioBuffer) return;
    try {
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();
      console.log('🔔 Sound played');
    } catch (error) {
      console.error('Play sound error:', error);
    }
  };

  useEffect(() => {
    if (!socket) return;
    const onConnect = () => setIsSocketConnected(true);
    const onDisconnect = () => setIsSocketConnected(false);
    if (socket.connected) setIsSocketConnected(true);
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    return () => {
      if (socket) {
        socket.off('connect', onConnect);
        socket.off('disconnect', onDisconnect);
      }
    };
  }, [socket]);

  useEffect(() => {
    if (!socket || !user || !isSocketConnected) return;

    const handleNewMessage = (data: any) => {
      // Не уведомляем о своих сообщениях
      if (data.sender_id === user.id) return;
      
      // Если открыт этот чат — не играем звук
      if (activeChatId === data.chat_id) {
        console.log('🔇 Sound suppressed: user in this chat');
        return;
      }
      
      console.log('🔔 Playing notification');
      playSound();
      
      // Мигание заголовка
      if (document.hidden) {
        let count = 0;
        const interval = setInterval(() => {
          document.title = count % 2 === 0 ? '💬 Новое сообщение!' : originalTitle.current;
          count++;
          if (count > 6) {
            clearInterval(interval);
            document.title = originalTitle.current;
          }
        }, 500);
        setTimeout(() => clearInterval(interval), 4000);
      }
    };

    socket.on('new_message', handleNewMessage);
    return () => {
      if (socket) socket.off('new_message', handleNewMessage);
      document.title = originalTitle.current;
    };
  }, [socket, user, isSocketConnected]);

  return null;
};

export default GlobalNotification;