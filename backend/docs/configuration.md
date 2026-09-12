# Configuração

## 1. Criar o ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Configurar MySQL

Edite o `.env` com a conexão do banco:

```env
DB_USER=USER
DB_PASS=PASSWORD
DB_HOST=localhost
DB_PORT=3306
DB_NAME=lapzap
```

## 3. Configurar JWT

Use um segredo forte e exclusivo fora do ambiente de desenvolvimento:

```env
JWT_SECRET_KEY=seu-segredo-longo-e-aleatorio
```

## 4. Configurar Evolution API

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-chave-da-evolution
EVOLUTION_INSTANCE_NAME=nome-da-instancia
```

- `EVOLUTION_API_URL` é o endereço base da Evolution API.
- `EVOLUTION_API_KEY` permanece somente no `.env`; ela não é enviada ao
  webhook, retornada pela API ou registrada em log.
- `EVOLUTION_INSTANCE_NAME` é o nome da instância conectada ao WhatsApp.

Na Evolution API, configure o webhook para enviar eventos a:

```text
POST https://SEU-DOMINIO/api/v1/webhooks/whatsapp
```

Em desenvolvimento local, use uma URL HTTPS pública de um túnel, como ngrok ou
Cloudflare Tunnel, porque uma instalação externa não consegue acessar
`localhost`.

## 5. Criar as tabelas e dados de desenvolvimento

Com o banco vazio:

```bash
alembic upgrade head
python -m app.database.seed
```

O seeder padrão cria `admin@example.com`, senha `123456` e telefones de
exemplo. Esses valores são somente para desenvolvimento.

## 6. Executar a API

```bash
uvicorn app.main:app --reload
```

- API: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>
