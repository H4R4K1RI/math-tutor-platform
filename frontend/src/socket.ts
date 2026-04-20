import { io, Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';

export let socket: Socket | null = null;

export const initSocket = () => {
  socket = io(SOCKET_URL, {
    transports: ['websocket'],
    withCredentials: true,  // ← ОТПРАВЛЯЕМ COOKIES С JWT
    autoConnect: false,     // ← НЕ ПОДКЛЮЧАЕМСЯ АВТОМАТИЧЕСКИ
  });
  
  socket.on('connect', () => console.log('Socket.IO connected'));
  socket.on('disconnect', () => console.log('Socket.IO disconnected'));
  socket.on('connect_error', (error) => console.error('Socket connection error:', error));
  
  return socket;
};

export const connectSocket = () => {
  if (socket && !socket.connected) {
    socket.connect();
  }
};

export const disconnectSocket = () => {
  if (socket && socket.connected) {
    socket.disconnect();
  }
};