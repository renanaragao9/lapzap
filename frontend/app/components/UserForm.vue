<script setup lang="ts">

const props = defineProps<{
  initialName?: string;
  initialEmail?: string;
  initialIsActive?: boolean;
  initialIsAdmin?: boolean;
  submitLabel: string;
  requirePassword: boolean;
  onSubmit: (payload: {
    name: string;
    email: string;
    password?: string;
    is_active: boolean;
    is_admin: boolean;
  }) => Promise<void>;
}>();

const name = ref(props.initialName ?? "");
const email = ref(props.initialEmail ?? "");
const password = ref("");
const isActive = ref(props.initialIsActive ?? true);
const isAdmin = ref(props.initialIsAdmin ?? false);
const error = ref("");
const loading = ref(false);

async function handleSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await props.onSubmit({
      name: name.value,
      email: email.value,
      password: props.requirePassword ? password.value : undefined,
      is_active: isActive.value,
      is_admin: isAdmin.value,
    });
  } catch (err: any) {
    error.value = err?.data?.detail ?? "Não foi possível salvar.";
    toast.error(error.value);
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
      <Label for="email">E-mail</Label>
      <Input id="email" v-model="email" type="email" required />
    </div>
    <div v-if="requirePassword" class="flex flex-col gap-1.5">
      <Label for="password">Senha</Label>
      <Input
        id="password"
        v-model="password"
        type="password"
        required
        minlength="6"
        autocomplete="new-password"
      />
    </div>
    <div class="flex items-center justify-between gap-2">
      <Label for="is_active">Ativo</Label>
      <Switch id="is_active" v-model="isActive" />
    </div>
    <div class="flex items-center justify-between gap-2">
      <Label for="is_admin">Administrador</Label>
      <Switch id="is_admin" v-model="isAdmin" />
    </div>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <div class="flex gap-2">
      <Button type="submit" class="flex-1" :disabled="loading">
        {{ loading ? "Salvando..." : submitLabel }}
      </Button>
      <Button as-child variant="outline" type="button">
        <NuxtLink to="/usuarios">Cancelar</NuxtLink>
      </Button>
    </div>
  </form>
</template>
