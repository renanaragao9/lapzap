<script setup lang="ts">
import { Loader2, Phone, Plus } from "lucide-vue-next";
import type { Business } from "~/types/business";

interface PhoneNumber {
  id: number;
  name: string;
  phone_number: string;
  is_active: boolean;
}

const route = useRoute();
const api = useApi();

// não tem seletor de negócio ainda (1 negócio por conta é o caso comum) -
// usa o business_id da URL, ou o primeiro negócio do usuário.
const { data: myBusinesses } = await useAsyncData("my-businesses", () =>
  api<Business[]>("/businesses/mine"),
);

const businessId = computed(() => {
  const fromQuery = Number(route.query.business_id);
  if (fromQuery) return fromQuery;
  return myBusinesses.value?.[0]?.id ?? null;
});

const {
  data: numbers,
  pending,
  refresh,
  error,
} = await useAsyncData(
  "numbers",
  () =>
    businessId.value
      ? api<PhoneNumber[]>("/numbers", {
          params: { business_id: businessId.value },
        })
      : Promise.resolve([]),
  { watch: [businessId] },
);

const removingId = ref<number | null>(null);
const dialogOpen = ref(false);
const pendingDelete = ref<PhoneNumber | null>(null);

function askRemove(n: PhoneNumber) {
  pendingDelete.value = n;
  dialogOpen.value = true;
}

async function confirmRemove(e: Event) {
  e.preventDefault();
  const target = pendingDelete.value;
  if (!target) return;
  removingId.value = target.id;
  try {
    await api(`/numbers/${target.id}`, { method: "DELETE" });
    dialogOpen.value = false;
    await refresh();
    toast.success("Número removido.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível remover o número.");
  } finally {
    removingId.value = null;
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
    >
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">
          Números autorizados
        </h1>
        <p class="text-sm text-muted-foreground">
          {{
            numbers?.length
              ? `${numbers.length} número${numbers.length > 1 ? "s" : ""} cadastrado${numbers.length > 1 ? "s" : ""}`
              : "Só importa quando o negócio está marcado como privado"
          }}
        </p>
      </div>
      <Button
        v-if="businessId"
        as-child
        class="w-full sm:w-auto"
      >
        <NuxtLink :to="`/numeros/novo?business_id=${businessId}`">
          <Plus class="size-4" />
          Novo número
        </NuxtLink>
      </Button>
    </div>

    <p v-if="!businessId && !pending" class="text-sm text-muted-foreground">
      Nenhum negócio vinculado à sua conta ainda.
    </p>

    <Card v-else class="overflow-hidden py-0">
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <p v-else-if="error" class="p-6 text-sm text-destructive">
        Não foi possível carregar os números.
      </p>

      <template v-else-if="numbers?.length">
        <div class="hidden sm:block">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Status</TableHead>
                <TableHead class="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="n in numbers" :key="n.id">
                <TableCell class="font-medium">{{ n.name }}</TableCell>
                <TableCell>
                  <span
                    class="inline-flex items-center gap-1.5 text-muted-foreground"
                  >
                    <Phone class="size-3.5" />
                    <span class="font-mono text-foreground">{{
                      n.phone_number
                    }}</span>
                  </span>
                </TableCell>
                <TableCell>
                  <Badge :variant="n.is_active ? 'default' : 'outline'">
                    {{ n.is_active ? "Ativo" : "Inativo" }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div class="flex justify-end">
                    <RowActions
                      :to="`/numeros/${n.id}`"
                      :removing="removingId === n.id"
                      @remove="askRemove(n)"
                    />
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div class="divide-y sm:hidden">
          <div
            v-for="n in numbers"
            :key="n.id"
            class="flex items-center justify-between gap-3 p-4"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <p class="truncate font-medium">{{ n.name }}</p>
                <Badge :variant="n.is_active ? 'default' : 'outline'">
                  {{ n.is_active ? "Ativo" : "Inativo" }}
                </Badge>
              </div>
              <p
                class="mt-0.5 flex items-center gap-1.5 text-sm text-muted-foreground"
              >
                <Phone class="size-3.5 shrink-0" />
                <span class="truncate font-mono text-foreground">{{
                  n.phone_number
                }}</span>
              </p>
            </div>
            <RowActions
              :to="`/numeros/${n.id}`"
              :removing="removingId === n.id"
              @remove="askRemove(n)"
            />
          </div>
        </div>
      </template>

      <div v-else class="flex flex-col items-center gap-3 py-16 text-center">
        <div
          class="flex size-10 items-center justify-center rounded-full bg-muted"
        >
          <Phone class="size-5 text-muted-foreground" />
        </div>
        <div>
          <p class="text-sm font-medium">Nenhum número cadastrado</p>
          <p class="text-sm text-muted-foreground">
            Adicione um número autorizado pra começar a receber mensagens.
          </p>
        </div>
        <Button as-child size="sm" class="mt-1">
          <NuxtLink :to="`/numeros/novo?business_id=${businessId}`">
            <Plus class="size-4" />
            Novo número
          </NuxtLink>
        </Button>
      </div>
    </Card>

    <ConfirmDeleteDialog
      v-model:open="dialogOpen"
      title="Remover número?"
      :subject="pendingDelete?.name"
      :loading="removingId !== null"
      @confirm="confirmRemove"
    >
      ({{ pendingDelete?.phone_number }}) deixa de poder enviar mensagens. Essa
      ação não pode ser desfeita.
    </ConfirmDeleteDialog>
  </div>
</template>
