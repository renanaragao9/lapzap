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
  loading.value = true;
  try {
    await props.onSubmit({ name: name.value, phone_number: phoneNumber.value });
  } catch (err: any) {
    error.value = err?.data?.detail ?? "Não foi possível salvar.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="field">
      <label for="name">Nome</label>
      <input id="name" v-model="name" required maxlength="255" />
    </div>
    <div class="field">
      <label for="phone_number">Número (formato +DDI DDD número)</label>
      <input
        id="phone_number"
        v-model="phoneNumber"
        required
        placeholder="+5585999999999"
        pattern="^\+[1-9]\d{7,14}$"
      />
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <button type="submit" :disabled="loading">
      {{ loading ? "Salvando..." : submitLabel }}
    </button>
  </form>
</template>
