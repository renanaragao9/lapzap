<script setup lang="ts">
const { token, logout } = useAuth();
const route = useRoute();

function handleLogout() {
  logout();
  navigateTo("/login");
}
</script>

<template>
  <div class="min-h-screen">
    <NuxtRouteAnnouncer />
    <header
      v-if="token && route.path !== '/login'"
      class="flex items-center gap-6 border-b bg-card px-6 py-3"
    >
      <strong>LapZap</strong>
      <nav class="flex-1">
        <NuxtLink to="/numbers" class="text-sm hover:underline"
          >Números</NuxtLink
        >
      </nav>
      <Button variant="outline" size="sm" @click="handleLogout">Sair</Button>
    </header>
    <main class="mx-auto max-w-2xl p-6">
      <NuxtPage />
    </main>
  </div>
</template>
