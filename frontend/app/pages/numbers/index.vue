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
  <Card>
    <CardHeader class="flex items-center justify-between">
      <CardTitle>Números autorizados</CardTitle>
      <Button as-child size="sm">
        <NuxtLink to="/numbers/new">Novo número</NuxtLink>
      </Button>
    </CardHeader>
    <CardContent>
      <p v-if="error" class="text-sm text-destructive">
        Não foi possível carregar os números.
      </p>

      <Table v-else-if="numbers?.length">
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Número</TableHead>
            <TableHead>Ativo</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="n in numbers" :key="n.id">
            <TableCell>{{ n.name }}</TableCell>
            <TableCell>{{ n.phone_number }}</TableCell>
            <TableCell>{{ n.is_active ? "Sim" : "Não" }}</TableCell>
            <TableCell class="flex justify-end gap-2">
              <Button as-child variant="outline" size="sm">
                <NuxtLink :to="`/numbers/${n.id}`">Editar</NuxtLink>
              </Button>
              <Button variant="destructive" size="sm" @click="remove(n.id)">
                Remover
              </Button>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <p v-else class="text-sm text-muted-foreground">
        Nenhum número cadastrado.
      </p>
    </CardContent>
  </Card>
</template>
