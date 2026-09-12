<script setup lang="ts">
const { token, logout } = useAuth();
const route = useRoute();

function handleLogout() {
  logout();
  navigateTo("/login");
}
</script>

<template>
  <div class="app">
    <NuxtRouteAnnouncer />
    <header v-if="token && route.path !== '/login'" class="topbar">
      <strong>LapZap</strong>
      <nav>
        <NuxtLink to="/numbers">Números</NuxtLink>
      </nav>
      <button type="button" @click="handleLogout">Sair</button>
    </header>
    <main>
      <NuxtPage />
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  font-family: system-ui, sans-serif;
  color: #1a1a1a;
  background: #f7f7f8;
}
.app {
  min-height: 100vh;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: #1a1a2e;
  color: white;
}
.topbar nav {
  flex: 1;
}
.topbar a {
  color: white;
}
.topbar button {
  background: transparent;
  border: 1px solid #666;
  color: white;
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}
main {
  max-width: 720px;
  margin: 0 auto;
  padding: 1.5rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
}
.field input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.error {
  color: #b3261e;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 1px solid #ddd;
}
button,
.button {
  cursor: pointer;
}
</style>
