<script setup lang="ts">
import { Wrench } from "lucide-vue-next";

definePageMeta({ middleware: "tenant" });

const BUSINESS_TYPE_LABELS: Record<string, string> = {
  barbearia: "Barbearia",
  loja: "Loja",
  generico: "Outro",
};

const api = useApi();
const { data: businesses } = await useMyBusiness();
const business = computed(() => businesses.value?.[0] ?? null);

const visibility = ref<"public" | "private">("public");
const savingVisibility = ref(false);

const creating = ref(false);
const createError = ref("");
const qrcodeBase64 = ref("");

const { data: info } = await useAsyncData("my-business-info", () =>
  business.value
    ? api<{ content: string }>(`/businesses/${business.value.id}/info`).catch(
        () => null,
      )
    : Promise.resolve(null),
);
const infoContent = ref(info.value?.content ?? "");
const savingInfo = ref(false);

watchEffect(() => {
  if (business.value) visibility.value = business.value.visibility;
});

async function saveInfo() {
  if (!business.value) return;
  savingInfo.value = true;
  try {
    await api(`/businesses/${business.value.id}/info`, {
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

async function createInstance() {
  if (!business.value) return;
  createError.value = "";
  qrcodeBase64.value = "";
  creating.value = true;
  try {
    const result = await api<{
      evolution_instance_name: string;
      qrcode_base64: string;
    }>(`/businesses/${business.value.id}/create-instance`, { method: "POST" });
    qrcodeBase64.value = result.qrcode_base64;
    await refreshNuxtData("my-businesses");
    toast.success("Instância criada. Escaneie o QR code pra conectar.");
  } catch (err: any) {
    createError.value =
      err?.data?.detail ?? "Não foi possível criar a instância.";
  } finally {
    creating.value = false;
  }
}

async function saveVisibility() {
  if (!business.value) return;
  savingVisibility.value = true;
  try {
    await api(`/businesses/${business.value.id}/visibility`, {
      method: "POST",
      body: { visibility: visibility.value },
    });
    await refreshNuxtData("my-businesses");
    toast.success("Visibilidade atualizada.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível atualizar.");
  } finally {
    savingVisibility.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col gap-4">
    <Card v-if="business">
      <CardHeader class="flex-row items-center gap-3 space-y-0">
        <div class="flex size-9 items-center justify-center rounded-full bg-muted">
          <Wrench class="size-4 text-foreground" />
        </div>
        <div>
          <CardTitle>{{ business.name }}</CardTitle>
          <CardDescription>
            {{ BUSINESS_TYPE_LABELS[business.business_type] ?? business.business_type }}
            · {{ business.contact_phone_number }} · plano {{ business.plan }}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent class="flex flex-col gap-4">
        <div class="flex items-center justify-between rounded-lg border p-3 text-sm">
          <span class="text-muted-foreground">Status</span>
          <Badge :variant="business.status === 'active' ? 'default' : 'outline'">
            {{ business.status === "active" ? "Ativo" : "Pendente de ativação" }}
          </Badge>
        </div>

        <div
          v-if="business.status !== 'active'"
          class="flex flex-col gap-3 rounded-lg border p-3"
        >
          <p class="text-sm text-muted-foreground">
            {{
              business.evolution_instance_name
                ? "Instância criada - aguardando aprovação do admin pra ativar de vez."
                : "Conecte o WhatsApp do seu negócio pra começar a atender."
            }}
          </p>
          <Button :disabled="creating" @click="createInstance">
            {{
              creating
                ? "Criando instância..."
                : business.evolution_instance_name
                  ? "Gerar novo QR code"
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
            <img :src="qrcodeBase64" alt="QR code do WhatsApp" class="size-48" />
            <p class="text-center text-xs text-muted-foreground">
              Escaneie com o WhatsApp do negócio (Aparelhos conectados →
              Conectar um aparelho).
            </p>
          </div>
        </div>

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
              :disabled="savingVisibility || visibility === business.visibility"
              @click="saveVisibility"
            >
              {{ savingVisibility ? "Salvando..." : "Salvar" }}
            </Button>
          </div>
          <NuxtLink
            v-if="visibility === 'private'"
            :to="`/numeros?business_id=${business.id}`"
            class="text-xs text-primary hover:underline"
          >
            Gerenciar números autorizados →
          </NuxtLink>
        </div>

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
            Esse texto vira contexto extra pro LLM responder seus clientes.
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

        <BusinessIntegrations :business-id="business.id" />
      </CardContent>
    </Card>
  </div>
</template>
