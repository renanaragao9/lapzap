<script setup lang="ts">
import { Loader2, MessageSquare, RefreshCw } from "lucide-vue-next";
import type { MessageLog } from "~/types/message-log";

const api = useApi();
const {
  data: messages,
  pending,
  refresh,
  error,
} = await useAsyncData("messages", () => api<MessageLog[]>("/messages"));
</script>

<template>
  <div class="flex flex-col gap-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">Mensagens</h1>
        <p class="text-sm text-muted-foreground">
          {{
            messages?.length
              ? `${messages.length} mensagem${messages.length > 1 ? "ns" : ""} recebida${messages.length > 1 ? "s" : ""}`
              : "Mensagens recebidas dos seus números autorizados"
          }}
        </p>
      </div>
      <Button
        variant="outline"
        class="w-full sm:w-auto"
        :disabled="pending"
        @click="refresh()"
      >
        <RefreshCw class="size-4" :class="{ 'animate-spin': pending }" />
        Atualizar
      </Button>
    </div>

    <Card class="overflow-hidden py-0">
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <p v-else-if="error" class="p-6 text-sm text-destructive">
        Não foi possível carregar as mensagens.
      </p>

      <div v-else-if="messages?.length" class="divide-y">
        <MessageItem v-for="m in messages" :key="m.id" :message="m" />
      </div>

      <div v-else class="flex flex-col items-center gap-3 py-16 text-center">
        <div
          class="flex size-10 items-center justify-center rounded-full bg-muted"
        >
          <MessageSquare class="size-5 text-muted-foreground" />
        </div>
        <div>
          <p class="text-sm font-medium">Nenhuma mensagem recebida</p>
          <p class="text-sm text-muted-foreground">
            Mensagens enviadas pro WhatsApp autorizado aparecem aqui.
          </p>
        </div>
      </div>
    </Card>
  </div>
</template>
