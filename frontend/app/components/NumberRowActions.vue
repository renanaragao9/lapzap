<script setup lang="ts">
import { Loader2, PencilLine, Trash2 } from "lucide-vue-next";

defineProps<{
  id: number;
  removing: boolean;
}>();
defineEmits<{
  remove: [];
}>();
</script>

<template>
  <div class="flex shrink-0 gap-1">
    <Button as-child variant="ghost" size="icon-sm" title="Editar">
      <NuxtLink :to="`/numbers/${id}`">
        <PencilLine class="size-4" />
      </NuxtLink>
    </Button>
    <Button
      variant="ghost"
      size="icon-sm"
      title="Remover"
      class="text-destructive hover:bg-destructive/10 hover:text-destructive"
      :disabled="removing"
      @click="$emit('remove')"
    >
      <Loader2 v-if="removing" class="size-4 animate-spin" />
      <Trash2 v-else class="size-4" />
    </Button>
  </div>
</template>
