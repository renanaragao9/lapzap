# Como testar

## Pré-requisitos

Ative o ambiente e instale as dependências:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Inicie a aplicação em outro terminal:

```bash
uvicorn app.main:app --reload
```

## Testes automatizados

```bash
pytest -q
```

Os testes cobrem:

- webhook da Evolution API: aceita payload de texto, retorna `200 OK` com
  `{"status": "ok"}` e não falha com payload incompleto ou com `data` em lista.
- autenticação: login válido, senha errada, e-mail inexistente, usuário
  inativo e rejeição de token ausente/inválido em rota protegida.
- números autorizados: criação, formato inválido (`422`), duplicidade
  (`409`), listagem restrita ao dono, número de outro usuário oculto (`404`),
  atualização e remoção.

Os testes de auth/números usam SQLite em memória (`aiosqlite`) no lugar do
MySQL, injetado via `app.dependency_overrides`.

## Testar saúde

```bash
curl -i http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

## Testar webhook da Evolution API

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "instance": "lapzap-dev",
    "data": {
      "key": {
        "remoteJid": "5585999999999@s.whatsapp.net",
        "id": "BAE5F001"
      },
      "messageType": "conversation",
      "message": {
        "conversation": "Olá, LapZap!"
      }
    }
  }'
```

Resposta esperada:

```json
{"status":"ok"}
```

Verifique o terminal do Uvicorn: ele deve registrar o payload e as informações
básicas da mensagem, como remetente, tipo, texto e ID.

## Testar payload incompleto

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"event":"connection.update"}'
```

Também deve retornar `200 OK`; campos ausentes não geram erro interno.
