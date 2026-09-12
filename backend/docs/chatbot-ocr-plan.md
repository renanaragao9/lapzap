# Plano: Chatbot da empresa + leitura de imagem com IA

Documento de arquitetura (sem código ainda). Decisões já tomadas:

- **LLM**: open source local via **Ollama** (não Claude/API paga)
- **Leitura de imagem**: **modelo de visão do próprio Ollama** (sem Tesseract/OCR separado — modelo lê a imagem direto)
- Fase atual: **plano**, implementação em conversa futura

## Hardware verificado nesta máquina

| Recurso | Valor | Nota |
|---|---|---|
| GPU | RTX 3050 6GB (laptop), driver 580.173.02 | Cabe modelo de visão quantizado ~7B (`llava:7b`, `minicpm-v`) — `llama3.2-vision:11b` é grande demais pra essa VRAM |
| RAM | 15GB total | **577MB livre no momento da análise** — precisa liberar antes de subir Ollama + modelo |
| Ollama | não instalado | precisa instalar |

## Fluxo ponta a ponta

```
WhatsApp (usuário manda texto ou foto)
  → Evolution API (Baileys) dispara webhook
  → POST /api/v1/webhooks/whatsapp (já existe, whatsapp/router.py)
  → WhatsAppService.process_webhook (já existe, hoje só loga/salva)
      ├─ se for TEXTO  → Chatbot: system prompt (info da empresa) + pergunta → Ollama (modelo texto) → resposta
      └─ se for IMAGEM → imagem (base64) + prompt vão direto pro Ollama (modelo de visão) → resposta
  → send_text() (já existe) → responde no WhatsApp via Evolution API
  → loga em MessageLog (OUTBOUND)
```

Só 1 modelo cuida de imagem+texto se usar um modelo de visão que também responde bem texto puro
(a maioria aceita as duas coisas) — evita manter dois modelos carregados na GPU ao mesmo tempo.

## Componentes novos a criar

### 1. `app/company/` — informação da empresa
- Fonte simples pra começar (YAGNI): um `.env` ou arquivo `company_info.md` com nome, produtos/serviços, horário, endereço, políticas etc — injetado como *system prompt* fixo.
- Não criar tabela de banco nem RAG/embeddings agora — só migrar pra isso se a base de conhecimento crescer (múltiplos documentos, PDFs, catálogo grande).

### 2. `app/llm/` — cliente Ollama (texto + visão)
- `ollama_client.py`: chama `POST http://localhost:11434/api/chat` via `httpx` (já é dependência do projeto, sem lib nova) — REST simples, sem SDK.
  - Mensagem de texto: `{"role": "user", "content": "..."}`.
  - Mensagem com imagem: `{"role": "user", "content": "...", "images": ["<base64>"]}` — campo `images` é como Ollama aceita input visual.
- `chat_service.py`: monta system prompt (info da empresa) + histórico curto (opcional, últimas N mensagens do `MessageLog` do mesmo `phone_number_id`) + pergunta/imagem → chama Ollama → retorna texto.
- Modelo sugerido: **`llava:7b`** (mais leve, cabe em 6GB) ou **`minicpm-v`** (alternativa mais nova/melhor custo-benefício) — usar o mesmo modelo pra texto puro e imagem, evita ter 2 modelos carregados.

### 3. Alterações no `whatsapp/service.py` existente
- `process_webhook` hoje só loga e sai (`is_message_event` + salva `MessageLog`, sem responder). Precisa:
  - Se `authorized=True` e `blocked=False`: rotear por `message_type`:
    - `TEXT` → chat texto puro no Ollama
    - `IMAGE` → pega base64 da mídia (`data.message.imageMessage` + Evolution manda a mídia se `webhookBase64=true` estiver ligado) → manda pro Ollama junto com prompt
  - Se `blocked`: não responder (comportamento atual mantido).

## Dependências novas (`requirements.txt`)

Nenhuma lib Python nova — tudo via `httpx` (já é dependência) chamando a API REST do Ollama.

Ollama é processo externo, instala separado:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llava:7b       # ou minicpm-v
ollama serve                # sobe em localhost:11434
```

## Config pendente antes de funcionar de ponta a ponta

1. **Liberar RAM** — só 577MB livre agora, Ollama + modelo visão precisa de ~5-6GB. Checar o que tá consumindo (containers Evolution API, Vite dev, etc) antes de subir.
2. **Webhook da instância Evolution precisa de `base64: true`** — hoje a config atual (`POST /webhook/set/:instance`) não tem isso, então imagem chega só como referência, não como bytes prontos pro modelo. Precisa atualizar a config do webhook.
3. Variáveis novas no `.env` do lapzap: `OLLAMA_URL=http://localhost:11434`, `OLLAMA_MODEL=llava:7b`.

## Riscos / limitações conhecidas

- Modelo open source 7B tem qualidade de resposta inferior a modelo de ponta (Claude/GPT) — ok pra Q&A simples de FAQ da empresa, pode alucinar em pergunta fora do escopo do system prompt (mitigar com instrução clara tipo "responda só sobre a empresa X, se não souber diga que vai encaminhar pra atendente").
- Modelo de visão 7B lê texto de imagem pior que Tesseract em documento limpo/bem escaneado, mas bem melhor em foto torta/mal iluminada de celular — trade-off aceito ao trocar OCR dedicado por modelo único.
- Rodar LLM local na mesma máquina que outros serviços dev (Evolution API, Postgres, etc) compete por RAM/GPU — se performance ficar ruim em uso simultâneo, considerar rodar Ollama em outra máquina/servidor.
