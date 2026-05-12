const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { createClient } = require('redis');
const { createAdapter } = require('@socket.io/redis-adapter');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const path = require('path');
const app = express();
const server = http.createServer(app);

// Servir a página de teste
const publicPath = path.join(__dirname, '..', 'public');
app.use(express.static(publicPath));

app.get('/health', (req, res) => {
    res.send('Realtime server is up and running!');
});

const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/0';
const pubClient = createClient({ url: REDIS_URL });
const subClient = pubClient.duplicate();

async function initRealtime() {
  await Promise.all([pubClient.connect(), subClient.connect()]);
  io.adapter(createAdapter(pubClient, subClient));

  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    console.log("Receiving connection attempt with token:", token ? "Present" : "Missing");
    
    if (!token) return next(new Error("Authentication error: No token provided"));
    
    try {
        const decoded = jwt.decode(token);
        console.log("Decoded token payload:", decoded);
        socket.companyId = decoded.company_id; 
        next();
    } catch (err) {
        console.error("JWT Decode Error:", err);
        next(new Error("Invalid token"));
    }
  });

  io.on('connection', (socket) => {
    console.log(`User connected: ${socket.id} to company ${socket.companyId}`);

    // Entrar na sala da empresa para receber eventos específicos
    if (socket.companyId) {
      socket.join(`company_${socket.companyId}`);
    }

    socket.on('disconnect', () => {
      console.log(`User disconnected: ${socket.id}`);
    });

    // Exemplo: Evento de digitando
    socket.on('typing', (data) => {
      // data: { ticket_id, is_typing }
      socket.to(`company_${socket.companyId}`).emit('user_typing', {
        ticket_id: data.ticket_id,
        user_id: socket.id,
        is_typing: data.is_typing
      });
    });
  });

  // Escutar eventos vindos do Backend via Redis Pub/Sub direto (alternativa ao adapter)
  // Útil para quando o Django publica algo fora do Socket.IO
  const internalSub = pubClient.duplicate();
  await internalSub.connect();
  await internalSub.subscribe('company_events', (message) => {
    const event = JSON.parse(message);
    // event: { company_id, type, payload }
    io.to(`company_${event.company_id}`).emit(event.type, event.payload);
  });

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Realtime server running on 0.0.0.0:${PORT}`);
  });
}

initRealtime().catch(console.error);
