<script setup lang="ts">
import { Loader2 } from "lucide-vue-next";

defineProps<{
  open: boolean;
  title: string;
  subject?: string;
  loading: boolean;
}>();
defineEmits<{
  "update:open": [boolean];
  confirm: [Event];
}>();
</script>

<template>
  <AlertDialog :open="open" @update:open="$emit('update:open', $event)">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>{{ title }}</AlertDialogTitle>
        <AlertDialogDescription>
          <strong class="text-foreground">{{ subject }}</strong>
          <slot />
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>Cancelar</AlertDialogCancel>
        <AlertDialogAction
          variant="destructive"
          :disabled="loading"
          @click="$emit('confirm', $event)"
        >
          <Loader2 v-if="loading" class="size-4 animate-spin" />
          {{ loading ? "Removendo..." : "Remover" }}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
