<script setup lang="ts">
const api = useApi();

async function create(payload: { name: string; phone_number: string }) {
  await api("/numbers", { method: "POST", body: payload });
  await navigateTo("/numbers");
}
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Novo número</CardTitle>
    </CardHeader>
    <CardContent>
      <PhoneNumberForm submit-label="Criar" :on-submit="create" />
    </CardContent>
  </Card>
</template>
