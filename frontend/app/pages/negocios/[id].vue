<script setup lang="ts">
import { ArrowLeft, Loader2, SearchX, Wrench } from "lucide-vue-next";
import type { Business } from "~/types/business";

definePageMeta({ middleware: "admin-only" });

const BUSINESS_TYPE_LABELS: Record<string, string> = {
  barbearia: "Barbearia",
  loja: "Loja",
  generico: "Outro",
};

const route = useRoute();
const api = useApi();
const id = route.params.id as string;

// não existe GET /businesses/{id} - só a listagem - acha o negócio nela.
const { data: businesses, pending } = await useAsyncData("businesses", () =>
  api<Business[]>("/businesses"),
);

const current = computed(
  () => businesses.value?.find((b) => b.id === Number(id)) ?? null,
);

const instanceName = ref("");
const submitError = ref("");
const submitting = ref(false);

watchEffect(() => {
  if (current.value) instanceName.value = current.value.evolution_instance_name ?? "";
});

async function activate() {
  submitError.value = "";
  if (!instanceName.value.trim()) {
    submitError.value = "Informe o nome da instância no Evolution API.";
    return;
  }
  submitting.value = true;
  try {
    await api(`/businesses/${id}/activate`, {
      method: "POST",
      body: { evolution_instance_name: instanceName.value.trim() },
    });
    toast.success("Negócio ativado.");
    await refreshNuxtData("businesses");
    await navigateTo("/negocios");
  } catch (err: any) {
    submitError.value = err?.data?.detail ?? "Não foi possível ativar.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col gap-4">
    <NuxtLink
      to="/negocios"
      class="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft class="size-4" />
      Voltar
    </NuxtLink>

    <Card>
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <template v-else-if="!current">
        <CardContent class="flex flex-col items-center gap-3 py-10 text-center">
          <div class="flex size-10 items-center justify-center rounded-full bg-muted">
            <SearchX class="size-5 text-muted-foreground" />
          </div>
          <p class="text-sm font-medium">Negócio não encontrado</p>
          <Button as-child variant="outline" size="sm">
            <NuxtLink to="/negocios">Voltar pra lista</NuxtLink>
          </Button>
        </CardContent>
      </template>

      <template v-else>
        <CardHeader class="flex-row items-center gap-3 space-y-0">
          <div class="flex size-9 items-center justify-center rounded-full bg-muted">
            <Wrench class="size-4 text-foreground" />
          </div>
          <div>
            <CardTitle>{{ current.name }}</CardTitle>
            <CardDescription>
              {{ BUSINESS_TYPE_LABELS[current.business_type] ?? current.business_type }}
              · {{ current.contact_phone_number }} · plano {{ current.plan }}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form class="flex flex-col gap-4" @submit.prevent="activate">
            <div class="flex flex-col gap-1.5">
              <Label for="instance_name">Instância no Evolution API</Label>
              <Input
                id="instance_name"
                v-model="instanceName"
                required
                placeholder="ex: barbearia-do-ze"
              />
              <p class="text-xs text-muted-foreground">
                Crie/conecte a instância manualmente no Evolution Manager
                primeiro (escaneie o QR code), depois cole aqui o nome exato
                dela.
              </p>
            </div>

            <p v-if="submitError" class="text-sm text-destructive">
              {{ submitError }}
            </p>

            <Button type="submit" :disabled="submitting">
              {{
                submitting
                  ? "Salvando..."
                  : current.status === "active"
                    ? "Atualizar instância"
                    : "Ativar negócio"
              }}
            </Button>
          </form>
        </CardContent>
      </template>
    </Card>
  </div>
</template>
