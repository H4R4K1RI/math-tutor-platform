import { io, Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';

export const socket: Socket = io(SOCKET_URL, {
  transports: ['websocket'],
  autoConnect: true,
});

export const initSocket = () => {
  socket.on('connect', () => console.log('Socket.IO connected'));
  socket.on('disconnect', () => console.log('Socket.IO disconnected'));
  return socket;
};