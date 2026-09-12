<script setup lang="ts">
const { token, logout } = useAuth();
const { data: me } = await useCurrentUser();

function handleLogout() {
  logout();
  navigateTo("/login");
}
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header
      v-if="token"
      class="flex items-center gap-6 border-b bg-card px-6 py-3"
    >
      <div class="flex items-center gap-2">
        <img
          src="/logo-aragao-labs.jpeg"
          alt="AragaoLabs"
          class="size-7 rounded-md object-cover"
        />
        <strong>LapZap</strong>
      </div>
      <nav class="flex flex-1 gap-4">
        <NuxtLink
          to="/numeros"
          class="text-sm text-muted-foreground hover:text-foreground"
          active-class="font-semibold text-primary"
          >Números</NuxtLink
        >
        <NuxtLink
          to="/mensagens"
          class="text-sm text-muted-foreground hover:text-foreground"
          active-class="font-semibold text-primary"
          >Mensagens</NuxtLink
        >
        <NuxtLink
          v-if="me?.is_admin"
          to="/negocios"
          class="text-sm text-muted-foreground hover:text-foreground"
          active-class="font-semibold text-primary"
          >Negócios</NuxtLink
        >
        <NuxtLink
          v-if="me?.is_admin"
          to="/usuarios"
          class="text-sm text-muted-foreground hover:text-foreground"
          active-class="font-semibold text-primary"
          >Usuários</NuxtLink
        >
      </nav>
      <span v-if="me" class="text-sm text-muted-foreground"
        >Olá, {{ me.name }}</span
      >
      <Button variant="outline" size="sm" @click="handleLogout">Sair</Button>
    </header>
    <main class="mx-auto w-full max-w-2xl flex-1 p-6">
      <slot />
    </main>
    <footer
      class="flex items-center justify-center gap-1.5 border-t px-6 py-4 text-xs text-muted-foreground"
    >
      <img
        src="/logo-aragao-labs.jpeg"
        alt=""
        class="size-4 rounded object-cover"
      />
      AragaoLabs
    </footer>
  </div>
</template>
