<script setup lang="ts">
import { ArrowLeft, Loader2, PencilLine, SearchX } from "lucide-vue-next";

interface PhoneNumber {
  id: number;
  name: string;
  phone_number: string;
}

const route = useRoute();
const api = useApi();
const id = route.params.id as string;

const {
  data: phoneNumber,
  pending,
  error,
} = await useAsyncData(`number-${id}`, () =>
  api<PhoneNumber>(`/numbers/${id}`),
);

async function update(payload: { name: string; phone_number: string }) {
  await api(`/numbers/${id}`, { method: "PUT", body: payload });
  toast.success("Número atualizado.");
  await navigateTo("/numeros");
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col gap-4">
    <NuxtLink
      to="/numeros"
      class="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft class="size-4" />
      Voltar
    </NuxtLink>

    <Card>
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <template v-else-if="error">
        <CardContent class="flex flex-col items-center gap-3 py-10 text-center">
          <div
            class="flex size-10 items-center justify-center rounded-full bg-muted"
          >
            <SearchX class="size-5 text-muted-foreground" />
          </div>
          <p class="text-sm font-medium">Número não encontrado</p>
          <Button as-child variant="outline" size="sm">
            <NuxtLink to="/numeros">Voltar pra lista</NuxtLink>
          </Button>
        </CardContent>
      </template>

      <template v-else-if="phoneNumber">
        <CardHeader class="flex-row items-center gap-3 space-y-0">
          <div
            class="flex size-9 items-center justify-center rounded-full bg-muted"
          >
            <PencilLine class="size-4 text-foreground" />
          </div>
          <div>
            <CardTitle>Editar número</CardTitle>
            <CardDescription>{{ phoneNumber.phone_number }}</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <PhoneNumberForm
            submit-label="Salvar"
            :initial-name="phoneNumber.name"
            :initial-phone-number="phoneNumber.phone_number"
            :on-submit="update"
          />
        </CardContent>
      </template>
    </Card>
  </div>
</template>
