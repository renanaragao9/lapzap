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

const { data: businesses, pending } = await useAsyncData("businesses", () =>
  api<Business[]>("/businesses"),
);

const current = computed(
  () => businesses.value?.find((b) => b.id === Number(id)) ?? null,
);

const instanceName = ref("");
const submitError = ref("");
const submitting = ref(false);

const creating = ref(false);
const createError = ref("");
const qrcodeBase64 = ref("");

const visibility = ref<"public" | "private">("public");
const savingVisibility = ref(false);

const infoContent = ref("");
const savingInfo = ref(false);

watchEffect(() => {
  if (current.value) {
    instanceName.value = current.value.evolution_instance_name ?? "";
    visibility.value = current.value.visibility;
  }
});

watchEffect(async () => {
  if (!current.value) return;
  const info = await api<{ content: string }>(
    `/businesses/${current.value.id}/info`,
  ).catch(() => null);
  infoContent.value = info?.content ?? "";
});

async function saveInfo() {
  if (!current.value) return;
  savingInfo.value = true;
  try {
    await api(`/businesses/${current.value.id}/info`, {
      method: "PUT",
      body: { content: infoContent.value },
    });
    toast.success("Informações salvas.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível salvar.");
  } finally {
    savingInfo.value = false;
  }
}

async function saveVisibility() {
  savingVisibility.value = true;
  try {
    await api(`/businesses/${id}/visibility`, {
      method: "POST",
      body: { visibility: visibility.value },
    });
    await refreshNuxtData("businesses");
    toast.success("Visibilidade atualizada.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível atualizar.");
  } finally {
    savingVisibility.value = false;
  }
}

async function createInstance() {
  // já tem instância ligada (ex: negócio já ativo e conectado de verdade) -
  // gerar uma nova troca o nome no banco e desconecta a instância atual
  if (
    current.value?.evolution_instance_name &&
    !confirm(
      `Já existe a instância "${current.value.evolution_instance_name}" conectada a esse negócio. ` +
        "Criar uma nova vai substituí-la e desconectar o WhatsApp atual. Continuar?",
    )
  ) {
    return;
  }

  createError.value = "";
  qrcodeBase64.value = "";
  creating.value = true;
  try {
    const result = await api<{
      evolution_instance_name: string;
      qrcode_base64: string;
    }>(`/businesses/${id}/create-instance`, { method: "POST" });
    qrcodeBase64.value = result.qrcode_base64;
    instanceName.value = result.evolution_instance_name;
    await refreshNuxtData("businesses");
    toast.success("Instância criada. Escaneie o QR code pra conectar.");
  } catch (err: any) {
    createError.value =
      err?.data?.detail ?? "Não foi possível criar a instância.";
  } finally {
    creating.value = false;
  }
}

async function activate() {
  submitError.value = "";
  submitting.value = true;
  try {
    // vazio = mantém a instância que já existe (dono criou sozinho) - só
    // manda quando quer vincular/trocar manualmente
    await api(`/businesses/${id}/activate`, {
      method: "POST",
      body: { evolution_instance_name: instanceName.value.trim() || null },
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
        <CardContent class="flex flex-col gap-6">
          <div class="flex flex-col gap-1.5 rounded-lg border p-3">
            <Label for="visibility">Visibilidade</Label>
            <div class="flex gap-2">
              <select
                id="visibility"
                v-model="visibility"
                class="dark:bg-input/30 border-input h-8 flex-1 rounded-lg border bg-transparent px-2.5 py-1 text-base outline-none md:text-sm"
              >
                <option value="public">Público (qualquer cliente recebe resposta)</option>
                <option value="private">Privado (só número autorizado)</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                :disabled="savingVisibility || visibility === current.visibility"
                @click="saveVisibility"
              >
                {{ savingVisibility ? "Salvando..." : "Salvar" }}
              </Button>
            </div>
            <NuxtLink
              v-if="visibility === 'private'"
              :to="`/numeros?business_id=${current.id}`"
              class="text-xs text-primary hover:underline"
            >
              Gerenciar números autorizados →
            </NuxtLink>
          </div>

          <div class="flex flex-col gap-3">
            <Button :disabled="creating" @click="createInstance">
              {{
                creating
                  ? "Criando instância..."
                  : current.evolution_instance_name
                    ? "Criar nova instância (gera novo QR code)"
                    : "Criar instância automaticamente"
              }}
            </Button>
            <p v-if="createError" class="text-sm text-destructive">
              {{ createError }}
            </p>

            <div
              v-if="qrcodeBase64"
              class="flex flex-col items-center gap-2 rounded-lg border p-4"
            >
              <img
                :src="qrcodeBase64"
                alt="QR code do WhatsApp"
                class="size-48"
              >
              <p class="text-center text-xs text-muted-foreground">
                Escaneie com o WhatsApp do negócio (Aparelhos conectados →
                Conectar um aparelho) pra ativar de verdade.
              </p>
            </div>
          </div>

          <div class="flex items-center gap-3 text-xs text-muted-foreground">
            <div class="h-px flex-1 bg-border" />
            ou vincule uma instância já existente
            <div class="h-px flex-1 bg-border" />
          </div>

          <form class="flex flex-col gap-4" @submit.prevent="activate">
            <div class="flex flex-col gap-1.5">
              <Label for="instance_name">Instância no Evolution API</Label>
              <Input
                id="instance_name"
                v-model="instanceName"
                placeholder="ex: barbearia-do-ze"
              />
              <p class="text-xs text-muted-foreground">
                Opcional - só preencha pra vincular manualmente uma instância
                criada no Evolution Manager. Se o dono já criou a própria
                instância, deixe em branco e só aprove.
              </p>
            </div>

            <p v-if="submitError" class="text-sm text-destructive">
              {{ submitError }}
            </p>

            <Button type="submit" variant="outline" :disabled="submitting">
              {{
                submitting
                  ? "Salvando..."
                  : current.status === "active"
                    ? "Atualizar instância"
                    : "Ativar negócio"
              }}
            </Button>
          </form>

          <div class="flex flex-col gap-1.5 rounded-lg border p-3">
            <Label for="info">Informações pro atendente (markdown)</Label>
            <textarea
              id="info"
              v-model="infoContent"
              rows="8"
              placeholder="Ex: aceitamos cartão e pix, não temos estacionamento, promoção de terça..."
              class="dark:bg-input/30 border-input focus-visible:border-ring focus-visible:ring-ring/50 w-full rounded-lg border bg-transparent px-2.5 py-1.5 text-base transition-colors focus-visible:ring-3 md:text-sm"
            />
            <p class="text-xs text-muted-foreground">
              Esse texto vira contexto extra pro LLM responder os clientes
              desse negócio.
            </p>
            <Button
              variant="outline"
              size="sm"
              class="w-fit"
              :disabled="savingInfo"
              @click="saveInfo"
            >
              {{ savingInfo ? "Salvando..." : "Salvar informações" }}
            </Button>
          </div>

          <BusinessIntegrations :business-id="current.id" />
        </CardContent>
      </template>
    </Card>
  </div>
</template>
