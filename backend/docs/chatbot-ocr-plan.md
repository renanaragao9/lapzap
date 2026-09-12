# Plano: Chatbot da empresa + leitura de imagem com IA

Documento de arquitetura (sem código ainda). Decisões já tomadas:

- **LLM**: open source local via **Ollama** (não Claude/API paga)
- **Leitura de imagem**: **modelo de visão do próprio Ollama** (sem Tesseract/OCR separado — modelo lê a imagem direto)
- **Modelo escolhido**: `minicpm-v` (testado contra `llava:7b` — llava recusava
  descrever foto com mão/pessoa visível mesmo em documento inofensivo,
  minicpm-v não teve esse problema e leu texto de documento melhor)
- Fase atual: **implementado e testado end-to-end com WhatsApp real**

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
- Modelo usado: **`minicpm-v`** — mesmo modelo pra texto puro e imagem, evita ter 2 modelos carregados.
- Prompt de imagem é **separado** do prompt de chat de texto: o system prompt
  de texto restringe a IA a "responder só sobre a empresa" (evita alucinação),
  mas essa mesma instrução fazia o modelo recusar descrever imagem enviada
  (achava que estava fora de escopo). `chat_service.py` usa um
  `IMAGE_SYSTEM_PROMPT` próprio, sem essa restrição, quando `image_base64` é
  passado.

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
ollama pull minicpm-v
ollama serve                # sobe em localhost:11434
```

## Config pendente antes de funcionar de ponta a ponta

1. **Liberar RAM** — só 577MB livre agora, Ollama + modelo visão precisa de ~5-6GB. Checar o que tá consumindo (containers Evolution API, Vite dev, etc) antes de subir.
2. **Webhook da instância Evolution precisa de `base64: true`** — hoje a config atual (`POST /webhook/set/:instance`) não tem isso, então imagem chega só como referência, não como bytes prontos pro modelo. Precisa atualizar a config do webhook.
3. Variáveis novas no `.env` do lapzap: `OLLAMA_URL=http://localhost:11434`, `OLLAMA_MODEL=minicpm-v`.
4. **Webhook precisa de `host.docker.internal`, não `localhost`, na URL** — o
   Evolution API roda em container; `localhost` ali é o próprio container, não
   o host onde o lapzap escuta. Ver `evo/README.md` (seção específica sobre
   isso) pro detalhe completo, inclusive o `extra_hosts` que precisa estar no
   `docker-compose.yaml` do Evolution API.
5. **Uvicorn do lapzap precisa escutar em `0.0.0.0`**, não só `127.0.0.1`
   (padrão do uvicorn) — senão o container não alcança mesmo com
   `host.docker.internal` certo.

## Bugs encontrados e corrigidos durante o teste real

- **Número de telefone não batia**: WhatsApp manda/recebe número BR com ou sem
  o 9º dígito móvel (`+5585997304827` vs `558597304827`, mesmo número). Busca
  em `numbers/service.py` era match exato de string — corrigido pra tentar as
  duas variações.
- **Resposta em espanhol**: modelo pequeno às vezes troca idioma. Corrigido
  reforçando "responda sempre em português" no topo do system prompt (onde o
  modelo dá mais atenção), não só no rodapé do `company/info.md`.
- **Chatbot recusava descrever imagem**: causado pelo próprio system prompt
  ("responda só sobre a empresa") — resolvido com `IMAGE_SYSTEM_PROMPT`
  separado (ver seção 2 acima).
- **`llava:7b` recusava foto com mão/pessoa visível** mesmo sendo só uma foto
  de documento seguro na mão — trocado pra `minicpm-v`, que não teve esse
  problema e leu o texto do documento com mais precisão.

## Riscos / limitações conhecidas

- Modelo open source tem qualidade de resposta inferior a modelo de ponta (Claude/GPT) — ok pra Q&A simples de FAQ da empresa, pode alucinar em pergunta fora do escopo do system prompt.
- Rodar LLM local na mesma máquina que outros serviços dev (Evolution API, Postgres, etc) compete por RAM/GPU — se performance ficar ruim em uso simultâneo, considerar rodar Ollama em outra máquina/servidor.
