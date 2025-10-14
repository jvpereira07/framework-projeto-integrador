# Sistema de Autenticação e Login - Documentação

## Visão Geral

O sistema de autenticação é baseado em uma arquitetura cliente-servidor com autenticação JWT (JSON Web Token). O servidor Node.js gerencia autenticação, persistência de dados e estado dos jogadores, enquanto o cliente Python lida com a interface do usuário e comunicação em tempo real.

---

## Estrutura do Sistema

### 1. Servidor (Node.js)
- **Base de Dados**: SQLite (`server/data-server.db`)
- **Rotas de Autenticação**: Express.js
- **Comunicação em Tempo Real**: Socket.IO
- **Criptografia**: bcrypt para senhas
- **Tokens**: JWT para sessões

### 2. Cliente (Python)
- **Interface**: Pygame/OpenGL
- **Comunicação**: Socket.IO Client
- **Estado**: Gerenciamento local do estado do jogo
- **Persistência**: Salvamento automático

---

## Fluxo de Autenticação

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Cliente   │         │   Servidor   │         │ Banco de    │
│   (Python)  │         │   (Node.js)  │         │   Dados    │
└─────┬───────┘         └──────┬───────┘         └─────┬───────┘
      │                        │                       │
      │   1. POST /login      │                       │
      │────────────────────>  │                       │
      │   {user, password}    │                       │
      │                       │    2. Verifica        │
      │                       │───────────────────>   │
      │                       │                       │
      │                       │    3. Retorna User    │
      │                       │ <─────────────────────│
      │                       │                       │
      │   4. JWT Token +      │                       │
      │ <────────────────────-│                       │
      │   Lista Personagens   │                       │
      │                       │                       │
      │  5. Conecta Socket.IO │                       │
      │   com JWT Token      │                       │
      │────────────────────>  │                       │
      │                       │                       │
      │   6. Confirmação     │                       │
      │ <─────────────────────│                       │
      │                       │                       │
```

---

## Banco de Dados

### Tabela User
```sql
CREATE TABLE "User" (
    "idUser" INTEGER PRIMARY KEY AUTOINCREMENT,
    "userName" TEXT UNIQUE NOT NULL,
    "email" TEXT UNIQUE NOT NULL,
    "senha" TEXT NOT NULL
)
```

### Tabela Player
```sql
CREATE TABLE "Player" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "idUser" INTEGER,
    "playername" TEXT,
    "level" INTEGER,
    "xp" INTEGER,
    "skillpoints" INTEGER,
    "maxHp" INTEGER,
    "hpRegen" INTEGER,
    "maxMana" INTEGER,
    "manaRegen" INTEGER,
    "maxStamina" INTEGER,
    "staminaRegen" INTEGER,
    "damage" INTEGER,
    "critical" INTEGER,
    "defense" INTEGER,
    "speed" INTEGER,
    "ace" INTEGER,
    "posx" INTEGER,
    "posy" INTEGER,
    "jsonInv" TEXT,
    "jsonEquips" TEXT,
    FOREIGN KEY(idUser) REFERENCES User(idUser)
)
```

---

## Rotas da API

### 1. POST /register
Registra um novo usuário no sistema.

**Request:**
```json
{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

**Response (201):**
```json
{
    "message": "Usuário criado com sucesso!"
}
```

### 2. POST /login
Autentica um usuário e retorna token JWT + personagens.

**Request:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response (200):**
```json
{
    "message": "Login bem-sucedido!",
    "token": "JWT_TOKEN",
    "user": {
        "id": "number",
        "username": "string",
        "email": "string"
    },
    "characters": [
        {
            "id": "number",
            "name": "string",
            "level": "number",
            ...
        }
    ]
}
```

### 3. POST /characters (Protegida)
Cria um novo personagem para o usuário autenticado.

**Headers:**
```
Authorization: Bearer JWT_TOKEN
```

**Request:**
```json
{
    "name": "string"
}
```

**Response (201):**
```json
{
    "id": "number",
    "name": "string",
    "level": "number",
    ...
}
```

### 4. PUT /player/state (Protegida)
Atualiza o estado de um personagem.

**Headers:**
```
Authorization: Bearer JWT_TOKEN
```

**Request:**
```json
{
    "character_id": "number",
    "position": {
        "x": "number",
        "y": "number"
    },
    "stats": {
        "maxHp": "number",
        "maxMana": "number",
        ...
    }
}
```

---

## Conexão Socket.IO

### Autenticação
```javascript
// Servidor
io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return next(new Error('Token inválido'));
        socket.user = user;
        next();
    });
});

// Cliente Python
auth_data = {
    'token': jwt_token,
    'character_id': selected_character.get('id')
}
sio.connect(base_url, auth=auth_data)
```

### Eventos

| Evento | Direção | Descrição |
|--------|----------|-----------|
| `connect` | Cliente → Servidor | Conexão inicial |
| `assign_id` | Servidor → Cliente | Atribui ID ao jogador |
| `game_state` | Servidor → Cliente | Atualiza estado do jogo |
| `player_input` | Cliente → Servidor | Envia inputs do jogador |
| `disconnect` | Ambos | Desconexão do jogador |

---

## Interface do Cliente

### Menu de Login
1. Opções iniciais:
   - Login
   - Cadastro
   - Sair

2. Fluxo de autenticação:
   - Input de usuário/senha
   - Tentativa de login
   - Seleção de personagem
   - Conexão com servidor de jogo

### Persistência de Estado
- Salvamento automático ao desconectar
- Atualização de posição e stats
- Cache local de token JWT

---

## Segurança

### 1. Senha
- Hashing com bcrypt
- Salt rounds: 10
- Armazenamento seguro no banco

### 2. JWT
- Token expira em 1 hora
- Verificação em todas rotas protegidas
- Necessário para conexão Socket.IO

### 3. Middleware de Autenticação
```javascript
function authenticateToken(req, res, next) {
    const token = req.headers['authorization']?.split(' ')[1];
    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
}
```

---

## Exemplos de Uso

### Login no Cliente
```python
# Entrada do usuário
ip = input("Digite o IP do servidor: ").strip() or "localhost"
base_url = f"http://{ip}:3000"

# Login
response = requests.post(f"{base_url}/login", json={
    "username": username,
    "password": password
})

if response.status_code == 200:
    data = response.json()
    jwt_token = data['token']
    characters = data['characters']
    
    # Conecta ao servidor de jogo
    auth_data = {
        'token': jwt_token,
        'character_id': selected_character['id']
    }
    sio.connect(base_url, auth=auth_data)
```

### Salvamento de Estado
```python
def save_player_state():
    if not all([game_state, my_player_id, jwt_token]):
        return
        
    player_data = game_state['players'][my_player_id]
    update_data = {
        'character_id': selected_character['id'],
        'position': {
            'x': player_data['x'],
            'y': player_data['y']
        },
        'stats': player_data['stats']
    }
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    requests.put(f"{base_url}/player/state",
                json=update_data,
                headers=headers)
```

---

## Pontos de Atenção

1. **Segurança**
   - Sempre use HTTPS em produção
   - Nunca armazene senhas em texto plano
   - Valide todos os inputs do cliente

2. **Desempenho**
   - Cache de token no cliente
   - Minimizar requisições de estado
   - Batch updates quando possível

3. **Consistência**
   - Salvamento automático na desconexão
   - Verificação de propriedade do personagem
   - Validação de dados do cliente

4. **Tolerância a Falhas**
   - Reconexão automática
   - Fallback para servidor local
   - Log de erros detalhado

---

## Troubleshooting

### Problemas Comuns

1. **Erro de Autenticação**
   - Verificar credenciais
   - Checar expiração do token
   - Validar formato do token

2. **Falha na Conexão Socket.IO**
   - Verificar URL do servidor
   - Confirmar token válido
   - Checar character_id

3. **Erro no Salvamento**
   - Validar estado do jogo
   - Confirmar autenticação
   - Verificar conexão com banco

### Logs Úteis
```python
print(f"[DEBUG] Conectando em {base_url}...")
print(f"[LOG] Token: {jwt_token[:10]}...")
print(f"[ERROR] Falha ao salvar: {error}")
```

---

## Conclusão

O sistema de autenticação fornece uma base segura e flexível para:
- Gerenciamento de usuários
- Persistência de dados
- Comunicação em tempo real
- Estado do jogo distribuído

A combinação de JWT para autenticação e Socket.IO para comunicação em tempo real permite uma experiência fluida e segura para o jogador.
