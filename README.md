# WhatsApp SaaS CRM - Base do Sistema

Este é o código inicial para um sistema SaaS de atendimento multiusuário via WhatsApp.

## Tecnologias Utilizadas
- **Backend:** Django + Django Rest Framework (Python 3.11)
- **Realtime:** Node.js + Socket.IO (Node 20)
- **Message Provider:** Evolution Go (evoapicloud/evolution-go)
- **Database:** PostgreSQL 15 (DBs: `whatsapp_saas`, `evogo_auth`, `evogo_users`)
- **Cache/PubSub:** Redis 7
- **Workers:** Celery

## Como rodar o projeto

1.  **Clone o repositório e configure o `.env`**:
    ```bash
    cp .env.example .env
    ```

2.  **Suba os containers** (Use `docker compose` em versões recentes):
    ```bash
    docker compose up --build
    ```

3.  **Rode as migrations iniciais**:
    ```bash
    docker-compose exec backend python manage.py makemigrations tickets
    docker-compose exec backend python manage.py migrate
    ```

4.  **Crie um superusuário (Admin)**:
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```

## Fluxo de Mensagens
1.  **Entrada:** Evolution API envia Webhook para `POST /api/v1/webhooks/evolution/`.
2.  **Processamento:** O Django enfileira uma tarefa no Celery.
3.  **Persistência:** A tarefa do Celery salva o contato, ticket e mensagem no Postgres.
4.  **Realtime:** Após salvar, o Celery publica um evento no Redis.
5.  **Socket.IO:** O servidor Node.js escuta o Redis e envia `new_message` para a sala da empresa (`company_{id}`).

## Endpoints Principais
- `POST /api/token/`: Obter token JWT.
- `GET /api/v1/tickets/`: Listar tickets da empresa do usuário.
- `POST /api/v1/tickets/{id}/send_message/`: Enviar mensagem para um cliente.
- `POST /api/v1/webhooks/evolution/`: Endpoint para receber eventos da Evolution API.

## Realtime (Socket.IO)
Conecte em `http://localhost:3000` enviando o token JWT no campo `auth: { token: '...' }`.
O servidor irá automaticamente colocar o socket na sala correta baseada no `company_id` presente no token.
