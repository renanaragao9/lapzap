<script setup lang="ts">
import { Image, MessageSquare, Phone } from "lucide-vue-next";
import type { MessageLog } from "~/types/message-log";

defineProps<{
  message: MessageLog;
}>();

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <div class="flex items-start gap-3 p-4">
    <div
      class="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted"
    >
      <Image
        v-if="message.message_type === 'IMAGE'"
        class="size-4 text-muted-foreground"
      />
      <MessageSquare v-else class="size-4 text-muted-foreground" />
    </div>

    <div class="min-w-0 flex-1">
      <div class="flex items-center justify-between gap-2">
        <span
          class="inline-flex items-center gap-1 text-xs text-muted-foreground"
        >
          <Phone class="size-3 shrink-0" />
          <span class="truncate font-mono">{{
            message.phone_number ?? "Número desconhecido"
          }}</span>
        </span>
        <span class="shrink-0 text-xs text-muted-foreground">{{
          formatTimestamp(message.created_at)
        }}</span>
      </div>

      <p class="mt-1 text-sm wrap-break-word">
        <template v-if="message.text">{{ message.text }}</template>
        <span v-else class="text-muted-foreground italic"
          >[{{ message.message_type.toLowerCase() }}]</span
        >
      </p>

      <Badge
        class="mt-2"
        :variant="message.blocked ? 'destructive' : 'default'"
      >
        {{ message.blocked ? "Bloqueada" : "Recebida" }}
      </Badge>
    </div>
  </div>
</template>
