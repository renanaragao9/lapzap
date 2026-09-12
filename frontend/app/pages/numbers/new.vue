<script setup lang="ts">
const api = useApi()

async function create(payload: { name: string; phone_number: string }) {
  await api('/numbers', { method: 'POST', body: payload })
  await navigateTo('/numbers')
}
</script>

<template>
  <div>
    <h1>Novo número</h1>
    <PhoneNumberForm submit-label="Criar" :on-submit="create" />
  </div>
</template>
