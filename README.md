# LapZap

Base inicial de estudos para uma futura integração:

`WhatsApp → Evolution API → FastAPI → OCR/IA → WhatsApp`

Documentação complementar:

- [Configuração](docs/configuration.md)
- [Como testar](docs/testing.md)

Nesta etapa, o projeto contém apenas uma API FastAPI com configuração por
variáveis de ambiente, uma rota de saúde e a base para persistência em MySQL.

## Requisitos

- Python 3.12 ou superior

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Defina as informações de conexão no `.env`. A aplicação monta internamente a
URL `mysql+asyncmy`:

```env
DB_USER=USER
DB_PASS=PASSWORD
DB_HOST=localhost
DB_PORT=3306
DB_NAME=lapzap
```

## Executar

```bash
uvicorn app.main:app --reload
```

Com a aplicação em execução:

- Saúde: <http://127.0.0.1:8000/health>
- Swagger: <http://127.0.0.1:8000/docs>

## Números autorizados

Após aplicar a migration, os números autorizados estão disponíveis nestas rotas:

- `POST /api/v1/numbers`
- `GET /api/v1/numbers`
- `GET /api/v1/numbers/{id}`
- `PUT /api/v1/numbers/{id}`
- `DELETE /api/v1/numbers/{id}`

Exemplo de criação:

```json
{
  "phone_number": "+5585999999999",
  "name": "Renan"
}
```

Fluxo de uma requisição:

```text
Request
  ↓
Route
  ↓
Schema (validação Pydantic)
  ↓
SQLAlchemy (modelo e AsyncSession)
  ↓
MySQL
  ↓
Response
```

Dados inválidos recebem `422`, um ID inexistente recebe `404` e um
`phone_number` duplicado recebe `409`.

## Banco de dados e migrations

O projeto usa SQLAlchemy assíncrono com `asyncmy`. A primeira migration cria a
tabela `phone_numbers`; a segunda cria `users` e associa cada número a um
usuário.

```bash
alembic upgrade head
```

Para desfazer somente essa migration inicial:

```bash
alembic downgrade -1
```

## Autenticação e números autorizados

Cada `phone_number` pertence obrigatoriamente a um usuário. As rotas de números
exigem um Bearer token e sempre filtram os dados por `current_user.id`; o
cliente não envia nem escolhe `user_id`.

Defina um segredo forte e exclusivo no `.env` antes de usar fora do ambiente de
desenvolvimento:

```env
JWT_SECRET_KEY=generate-a-long-random-secret-for-each-environment
```

Faça login com um usuário existente no banco:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "123456"
}
```

A resposta contém `access_token`. Envie-o nas rotas de números:

```http
Authorization: Bearer SEU_TOKEN
```

Fluxo de uma operação de números:

```text
Request
  ↓
Route
  ↓
Schema (Pydantic)
  ↓
get_current_user() valida o JWT
  ↓
SQLAlchemy filtra por current_user.id
  ↓
MySQL
  ↓
Response
```

Não há endpoint de criação de usuários nesta etapa; o primeiro usuário deve ser
inserido previamente com senha gerada por `hash_password()`.

## Configuração da Evolution API

Defina as variáveis no `.env`:

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE_NAME=
```

- `EVOLUTION_API_URL`: endereço base da Evolution API, sem credenciais.
- `EVOLUTION_API_KEY`: chave da Evolution API; mantenha-a somente no `.env`.
- `EVOLUTION_INSTANCE_NAME`: nome da instância WhatsApp configurada na
  Evolution API.

No painel ou na configuração da instância Evolution, aponte o webhook para:

```text
POST /api/v1/webhooks/whatsapp
```

O endpoint aceita um objeto JSON e registra o payload. Quando o evento é de
mensagem, ele também:

- checa se o remetente é um `phone_number` autorizado e ativo;
- checa se o remetente excedeu `RATE_LIMIT_PER_MINUTE` mensagens no último
  minuto;
- grava um `MessageLog` (payload bruto, tipo, remetente vinculado quando
  autorizado) marcado como `blocked=True` quando o remetente não é
  autorizado ou está em rate limit.

Ele não envia mensagens e não usa a API key.

Teste localmente:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","instance":"lapzap-dev","data":{"key":{"remoteJid":"5585999999999@s.whatsapp.net","id":"BAE5F001"},"messageType":"conversation","message":{"conversation":"Olá, LapZap!"}}}'
```

## Seed de desenvolvimento

Após aplicar as migrations, crie um usuário e seus números autorizados com:

```bash
python -m app.database.seed
```

O padrão de desenvolvimento cria `admin@example.com`, senha `123456` e dois
telefones de exemplo. Você pode sobrescrever qualquer valor:

```bash
python -m app.database.seed --name "Outro usuário" --email "outro@example.com" \
  --password "outra-senha" --phone "+5585977777777"
```

O comando armazena apenas o hash Argon2 da senha. Ele é idempotente: não cria
o mesmo usuário ou telefone duas vezes. Um telefone já associado a outro
usuário interrompe o seed para evitar transferência indevida de propriedade.

### Conceitos

- **Session:** unidade de trabalho do SQLAlchemy; acompanha alterações e é o
  meio pelo qual a aplicação conversa com o banco.
- **AsyncSession:** versão assíncrona da `Session`, usada com `await` para não
  bloquear o servidor enquanto espera pelo MySQL.
- **Model:** classe Python que mapeia uma tabela e suas colunas. Neste projeto,
  `PhoneNumber` representa `phone_numbers`.
- **Migration:** arquivo versionado que descreve uma mudança no schema do banco,
  com caminho de aplicação (`upgrade`) e reversão (`downgrade`).
- **Alembic:** ferramenta que executa e registra as migrations do SQLAlchemy,
  mantendo o schema do banco na versão esperada pelo código.

Resposta esperada de `GET /health`:

```json
{
  "status": "ok"
}
```
