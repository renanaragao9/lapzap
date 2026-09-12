<script setup lang="ts">
interface PhoneNumber {
  id: number;
  name: string;
  phone_number: string;
  is_active: boolean;
}

const api = useApi();
const {
  data: numbers,
  refresh,
  error,
} = await useAsyncData("numbers", () => api<PhoneNumber[]>("/numbers"));

async function remove(id: number) {
  if (!confirm("Remover este número?")) return;
  await api(`/numbers/${id}`, { method: "DELETE" });
  await refresh();
}
</script>

<template>
  <div>
    <div
      style="display: flex; justify-content: space-between; align-items: center"
    >
      <h1>Números autorizados</h1>
      <NuxtLink to="/numbers/new" class="button">Novo número</NuxtLink>
    </div>

    <p v-if="error" class="error">Não foi possível carregar os números.</p>

    <table v-else-if="numbers?.length">
      <thead>
        <tr>
          <th>Nome</th>
          <th>Número</th>
          <th>Ativo</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="n in numbers" :key="n.id">
          <td>{{ n.name }}</td>
          <td>{{ n.phone_number }}</td>
          <td>{{ n.is_active ? "Sim" : "Não" }}</td>
          <td>
            <NuxtLink :to="`/numbers/${n.id}`">Editar</NuxtLink>
            &nbsp;
            <button type="button" @click="remove(n.id)">Remover</button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else>Nenhum número cadastrado.</p>
  </div>
</template>
