# LapZap

Base inicial de estudos para uma futura integração:

`WhatsApp → Meta API → FastAPI → OCR/IA → WhatsApp`

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

## Webhook do WhatsApp Cloud API

O webhook está disponível em `/api/v1/webhooks/whatsapp` e possui dois métodos:

- `GET`: a Meta o chama uma vez ao configurar ou validar a URL. Ela envia
  `hub.mode=subscribe`, `hub.verify_token` e `hub.challenge`. Quando o token
  recebido é igual a `META_VERIFY_TOKEN`, a API devolve exatamente o valor de
  `hub.challenge` como texto puro; assim a Meta confirma que a URL pertence à
  aplicação configurada.
- `POST`: a Meta envia eventos como mensagens recebidas e atualizações de
  status em JSON. Nesta etapa, a API apenas registra o objeto recebido no log e
  responde `200 OK`, sem responder mensagens nem chamar a Graph API.

Configure no `.env`:

```env
META_VERIFY_TOKEN=choose-a-random-verify-token
META_ACCESS_TOKEN=replace-with-meta-access-token
META_PHONE_NUMBER_ID=replace-with-phone-number-id
META_API_VERSION=vXX.X
```

`META_VERIFY_TOKEN` é um segredo escolhido por você e informado também no
painel da Meta. Ele não é um token da Meta: serve apenas para a verificação do
GET. Os demais valores ficam configurados agora para uma futura chamada à API,
mas ainda não são usados.

### Teste local

Com a API em execução, teste a validação manualmente:

```bash
curl -i "http://127.0.0.1:8000/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=SEU_TOKEN&hub.challenge=desafio"
```

E simule um evento:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[]}'
```

A Meta não consegue alcançar `localhost`; para validar no painel dela, exponha
a porta local por um túnel HTTPS público, como ngrok ou Cloudflare Tunnel, e
cadastre a URL pública com o mesmo caminho.

### Autorização do remetente

Quando o POST contém mensagens recebidas, a aplicação extrai cada
`messages[].from`, adiciona o prefixo `+` (o formato usado em `phone_numbers`)
e chama `is_phone_authorized(phone_number)`.

```text
Meta
  ↓
Webhook
  ↓
extrair telefone
  ↓
buscar phone_numbers
  ↓
verificar is_active
  ↓
authorized / unauthorized
```

A consulta considera autorizado somente um registro com o mesmo telefone e
`is_active = true`. Telefones ausentes e telefones inativos são registrados como
`authorized=False`. Nesta etapa, a decisão é apenas registrada no log: nenhuma
mensagem é processada ou respondida.

### Logs de mensagens

Cada mensagem recebida gera um registro em `message_logs`, contendo o payload
original da Meta em JSON. Os valores iniciais são `direction="INBOUND"`,
`processed=false` e `blocked=true` quando o remetente não está autorizado.

O relacionamento no SQLAlchemy é um-para-muitos:

```text
PhoneNumber (1) ──< MessageLog (N)
```

`PhoneNumber.message_logs` representa a lista de logs daquele número, enquanto
`MessageLog.phone_number` aponta para o número que originou o log. No banco,
`message_logs.phone_number_id` é uma chave estrangeira para `phone_numbers.id`.
Esse campo pode ser `NULL` para manter logs de remetentes não autorizados. Se
um número for removido, `ON DELETE SET NULL` preserva os logs já recebidos.

### Limite de mensagens

`RATE_LIMIT_PER_MINUTE=10` define quantas mensagens recebidas de um número
ativo podem passar por minuto. Antes de gravar o log de uma mensagem, a API
conta os logs `INBOUND` daquele `phone_number_id` criados nos últimos 60
segundos.

- Menos de 10: o log é salvo com `blocked=false` e o fluxo permanece liberado.
- Dez ou mais: o novo log é salvo com `blocked=true`; não há processamento
  posterior nesta etapa.
- Número ausente ou inativo: também é salvo com `blocked=true`, sem aplicar o
  rate limit.

O controle usa apenas MySQL e SQLAlchemy. É apropriado para o estágio atual;
Redis poderá ser considerado depois se o volume ou a concorrência crescer.

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
# lapzap
