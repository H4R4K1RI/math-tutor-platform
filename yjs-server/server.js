import http from 'http';
import { WebSocketServer } from 'ws';
import * as Y from 'yjs';
import { setupWSConnection } from 'y-websocket/bin/utils';

const PORT = 5858;

const server = http.createServer((req, res) => {
  // Health check
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('y-websocket server');
});

const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
  console.log(`[y-websocket] connection from ${req.socket.remoteAddress}`);

  // y-websocket умеет работать с raw ws-сервером
  setupWSConnection(ws, req);
});

server.listen(PORT, () => {
  console.log(`y-websocket server started on port ${PORT}`);
});