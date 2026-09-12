<script setup lang="ts">
const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const { login } = useAuth();

async function handleSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await login(email.value, password.value);
    await navigateTo("/numbers");
  } catch {
    error.value = "E-mail ou senha inválidos.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div style="max-width: 320px; margin: 4rem auto">
    <h1>Entrar</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="email">E-mail</label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          autocomplete="username"
        />
      </div>
      <div class="field">
        <label for="password">Senha</label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
        />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? "Entrando..." : "Entrar" }}
      </button>
    </form>
  </div>
</template>
