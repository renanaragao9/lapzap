<script setup lang="ts">
const props = defineProps<{
  initialName?: string;
  initialPhoneNumber?: string;
  submitLabel: string;
  onSubmit: (payload: { name: string; phone_number: string }) => Promise<void>;
}>();

const name = ref(props.initialName ?? "");
const phoneNumber = ref(props.initialPhoneNumber ?? "");
const error = ref("");
const loading = ref(false);

async function handleSubmit() {
  error.value = "";
  if (!phoneNumber.value) {
    error.value = "Informe o DDD e os 9 dígitos do número.";
    return;
  }
  loading.value = true;
  try {
    await props.onSubmit({
      name: name.value,
      phone_number: phoneNumber.value,
    });
  } catch (err: any) {
    error.value = err?.data?.detail ?? "Não foi possível salvar.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
    <div class="flex flex-col gap-1.5">
      <Label for="name">Nome</Label>
      <Input id="name" v-model="name" required maxlength="255" />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="phone_number">Número</Label>
      <BrPhoneInput id="phone_number" v-model="phoneNumber" />
    </div>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <div class="flex gap-2">
      <Button type="submit" class="flex-1" :disabled="loading">
        {{ loading ? "Salvando..." : submitLabel }}
      </Button>
      <Button as-child variant="outline" type="button">
        <NuxtLink to="/numeros">Cancelar</NuxtLink>
      </Button>
    </div>
  </form>
</template>
