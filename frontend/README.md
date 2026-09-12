# LapZap — Frontend

Nuxt 4. Login e CRUD de números autorizados, consumindo a API FastAPI em
[`../backend`](../backend/README.md).

## Rodando

```bash
npm install
npm run dev
```

Abre em <http://localhost:3000>.

## Backend

O Nitro (servidor do Nuxt) faz proxy de `/api/**` para o backend, evitando
CORS. Por padrão aponta para `http://127.0.0.1:8000`; para mudar:

```bash
NUXT_API_BASE_URL=http://outro-host:8000 npm run dev
```

O backend precisa estar rodando (`uvicorn app.main:app --reload` dentro de
`../backend`) e com pelo menos um usuário existente (`python -m
app.database.seed`) para o login funcionar.

## Estrutura

- `app/pages/login.vue` — login, grava o token num cookie (`lapzap_token`).
- `app/middleware/auth.global.ts` — redireciona para `/login` quando não há
  token, em qualquer rota exceto `/login`.
- `app/composables/useAuth.ts` — token + login/logout.
- `app/composables/useApi.ts` — `$fetch` com `Authorization: Bearer` e
  logout automático em `401`.
- `app/pages/numbers/` — listar, criar, editar e remover números
  autorizados.

## Não incluído

- Cadastro de usuário (a API não expõe essa rota; ver `python -m
  app.database.seed` no backend).
- Refresh token (o token expira em `ACCESS_TOKEN_EXPIRE_MINUTES`; ao expirar,
  qualquer chamada cai em `401` e desloga).
