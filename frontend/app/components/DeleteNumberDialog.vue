<script setup lang="ts">
import { Loader2 } from "lucide-vue-next";

defineProps<{
  open: boolean;
  name?: string;
  phoneNumber?: string;
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
        <AlertDialogTitle>Remover número?</AlertDialogTitle>
        <AlertDialogDescription>
          <strong class="text-foreground">{{ name }}</strong>
          ({{ phoneNumber }}) deixa de poder enviar mensagens. Essa ação não
          pode ser desfeita.
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
