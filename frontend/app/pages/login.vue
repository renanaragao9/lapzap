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
  <div class="mx-auto mt-16 max-w-sm">
    <Card>
      <CardHeader>
        <CardTitle>Entrar</CardTitle>
      </CardHeader>
      <CardContent>
        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div class="flex flex-col gap-1.5">
            <Label for="email">E-mail</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              required
              autocomplete="username"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for="password">Senha</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
            />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" :disabled="loading">
            {{ loading ? "Entrando..." : "Entrar" }}
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
