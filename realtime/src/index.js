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
        socket.userId = decoded.user_id;
        next();
    } catch (err) {
        console.error("JWT Decode Error:", err);
        next(new Error("Invalid token"));
    }
  });

  const onlineUsers = new Map(); // userId -> Set of socket.id

  io.on('connection', async (socket) => {
    console.log(`User connected: ${socket.id} to company ${socket.companyId}`);

    // Entrar na sala da empresa para receber eventos específicos
    if (socket.companyId) {
      socket.join(`company_${socket.companyId}`);
    }

    if (socket.userId) {
      if (!onlineUsers.has(socket.userId)) {
        onlineUsers.set(socket.userId, new Set());
      }
      onlineUsers.get(socket.userId).add(socket.id);
      
      // Sync status from Redis or default to online
      const statusKey = `user_status_${socket.userId}`;
      let status = await pubClient.get(statusKey);
      if (!status) {
        status = 'online';
        await pubClient.set(statusKey, status, { EX: 90 });
      }
      
      socket.userStatus = status;
      
      const activeKey = `user_active_${socket.userId}`;
      if (status !== 'offline') {
        await pubClient.set(activeKey, Math.floor(Date.now() / 1000), { EX: 90 });
      } else {
        await pubClient.del(activeKey);
      }
      
      const displayStatus = status === 'online' ? 'Online' : (status === 'away' ? 'Ausente' : 'Offline');
      io.to(`company_${socket.companyId}`).emit('user_status_changed', {
        user_id: socket.userId,
        status: displayStatus
      });
      
      socket.emit('status_sync', { status });
    }

    // Handle manual status changes
    socket.on('change_status', async (data) => {
      if (socket.userId) {
        console.log(`User ${socket.userId} status changed to ${data.status}`);
        socket.userStatus = data.status;
        
        const activeKey = `user_active_${socket.userId}`;
        const statusKey = `user_status_${socket.userId}`;
        
        await pubClient.set(statusKey, data.status, { EX: 90 });
        
        if (data.status === 'offline') {
          await pubClient.del(activeKey);
        } else {
          await pubClient.set(activeKey, Math.floor(Date.now() / 1000), { EX: 90 });
        }
        
        const displayStatus = data.status === 'online' ? 'Online' : (data.status === 'away' ? 'Ausente' : 'Offline');
        io.to(`company_${socket.companyId}`).emit('user_status_changed', {
          user_id: socket.userId,
          status: displayStatus
        });
      }
    });

    socket.on('disconnect', async () => {
      console.log(`User disconnected: ${socket.id}`);
      if (socket.userId && onlineUsers.has(socket.userId)) {
        const sockets = onlineUsers.get(socket.userId);
        sockets.delete(socket.id);
        if (sockets.size === 0) {
          onlineUsers.delete(socket.userId);
          
          const activeKey = `user_active_${socket.userId}`;
          const statusKey = `user_status_${socket.userId}`;
          
          await pubClient.del(activeKey);
          await pubClient.del(statusKey);
          
          io.to(`company_${socket.companyId}`).emit('user_status_changed', {
            user_id: socket.userId,
            status: 'Offline'
          });
        }
      }
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

  // Periodically refresh Redis TTL for online/active users
  setInterval(async () => {
    try {
      for (const [userId, sockets] of onlineUsers.entries()) {
        if (sockets.size > 0) {
          const statusKey = `user_status_${userId}`;
          const status = await pubClient.get(statusKey) || 'online';
          
          await pubClient.expire(statusKey, 90);
          if (status !== 'offline') {
            const activeKey = `user_active_${userId}`;
            await pubClient.expire(activeKey, 90);
          }
        }
      }
    } catch (err) {
      console.error("Error refreshing active users TTL:", err);
    }
  }, 30000);

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Realtime server running on 0.0.0.0:${PORT}`);
  });
}

initRealtime().catch(console.error);
