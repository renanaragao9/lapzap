<script setup lang="ts">
definePageMeta({ layout: "blank" });

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
    await navigateTo("/numeros");
  } catch {
    error.value = "E-mail ou senha inválidos.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="dark relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6"
  >
    <div
      class="absolute inset-0 [background-image:radial-gradient(var(--color-white)_1px,transparent_1px)]/8 bg-size-[24px_24px]"
    />
    <div
      class="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-primary/20 blur-3xl"
    />
    <div
      class="absolute -right-32 -bottom-32 h-96 w-96 rounded-full bg-primary/10 blur-3xl"
    />

    <div class="relative flex w-full max-w-sm flex-col items-center gap-6">
      <div class="flex items-center gap-2.5">
        <img
          src="/logo-aragao-labs.jpeg"
          alt="AragaoLabs"
          class="size-9 rounded-lg object-cover"
        />
        <span class="text-lg font-semibold text-foreground">LapZap</span>
      </div>

      <Card
        class="w-full border-white/10 bg-card/60 backdrop-blur-xl supports-backdrop-filter:bg-card/40"
      >
        <CardHeader>
          <CardTitle>Entrar</CardTitle>
          <CardDescription
            >Acesse com sua conta pra gerenciar os números
            autorizados.</CardDescription
          >
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
                placeholder="voce@empresa.com"
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
                placeholder="••••••••"
              />
            </div>
            <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
            <Button type="submit" class="mt-2 w-full" :disabled="loading">
              {{ loading ? "Entrando..." : "Entrar" }}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
