<script setup lang="ts">
import { CircleCheck, CircleX } from "lucide-vue-next";

const toasts = useToasts();
</script>

<template>
  <div class="fixed top-4 right-4 z-50 flex w-80 flex-col gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="flex items-start gap-2 rounded-lg border bg-popover p-3 text-sm text-popover-foreground shadow-lg"
      >
        <CircleCheck
          v-if="t.type === 'success'"
          class="mt-0.5 size-4 shrink-0 text-primary"
        />
        <CircleX v-else class="mt-0.5 size-4 shrink-0 text-destructive" />
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
