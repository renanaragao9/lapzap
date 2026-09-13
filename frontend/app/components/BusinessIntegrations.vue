<script setup lang="ts">
import { Loader2, Plug, Plus, Trash2 } from "lucide-vue-next";
import type { BusinessIntegration, IntegrationType } from "~/types/business";

const props = defineProps<{ businessId: number }>();

const TYPE_LABELS: Record<IntegrationType, string> = {
  google_calendar: "Google Calendar",
  outlook_calendar: "Calendário Outlook",
  generic: "Genérica",
};

const SELECT_CLASS =
  "dark:bg-input/30 border-input focus-visible:border-ring focus-visible:ring-ring/50 h-8 rounded-lg border bg-transparent px-2.5 py-1 text-base transition-colors focus-visible:ring-3 md:text-sm w-full min-w-0 outline-none";

const api = useApi();
const dataKey = computed(() => `integrations-${props.businessId}`);
const { data: integrations, refresh } = await useAsyncData(
  dataKey.value,
  () => api<BusinessIntegration[]>(`/businesses/${props.businessId}/integrations`),
);

const showForm = ref(false);
const editingId = ref<number | null>(null);
const name = ref("");
const type = ref<IntegrationType>("google_calendar");
const host = ref("");
const email = ref("");
const secret = ref("");
const saving = ref(false);
const formError = ref("");

const removingId = ref<number | null>(null);
const dialogOpen = ref(false);
const pendingDelete = ref<BusinessIntegration | null>(null);

function resetForm() {
  editingId.value = null;
  name.value = "";
  type.value = "google_calendar";
  host.value = "";
  email.value = "";
  secret.value = "";
  formError.value = "";
}

function startEdit(integration: BusinessIntegration) {
  editingId.value = integration.id;
  name.value = integration.name;
  type.value = integration.type;
  host.value = integration.host ?? "";
  email.value = integration.email ?? "";
  secret.value = "";
  showForm.value = true;
}

async function save() {
  formError.value = "";
  saving.value = true;
  try {
    const body = {
      name: name.value,
      type: type.value,
      host: host.value || null,
      email: email.value || null,
      ...(secret.value ? { secret: secret.value } : {}),
    };
    if (editingId.value) {
      await api(`/businesses/${props.businessId}/integrations/${editingId.value}`, {
        method: "PUT",
        body,
      });
    } else {
      await api(`/businesses/${props.businessId}/integrations`, {
        method: "POST",
        body,
      });
    }
    await refresh();
    showForm.value = false;
    resetForm();
    toast.success("Integração salva.");
  } catch (err: any) {
    formError.value = err?.data?.detail ?? "Não foi possível salvar.";
  } finally {
    saving.value = false;
  }
}

function askRemove(integration: BusinessIntegration) {
  pendingDelete.value = integration;
  dialogOpen.value = true;
}

async function confirmRemove(e: Event) {
  e.preventDefault();
  const target = pendingDelete.value;
  if (!target) return;
  removingId.value = target.id;
  try {
    await api(`/businesses/${props.businessId}/integrations/${target.id}`, {
      method: "DELETE",
    });
    dialogOpen.value = false;
    await refresh();
    toast.success("Integração removida.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível remover.");
  } finally {
    removingId.value = null;
  }
}
</script>

<template>
  <div class="flex flex-col gap-3 rounded-lg border p-3">
    <div class="flex items-center justify-between">
      <Label>Integrações (calendário, APIs externas)</Label>
      <Button
        size="sm"
        variant="outline"
        @click="
          showForm ? (showForm = false) : ((resetForm(), (showForm = true)))
        "
      >
        <Plus class="size-4" />
        {{ showForm ? "Cancelar" : "Nova" }}
      </Button>
    </div>
    <p class="text-xs text-muted-foreground">
      Guarda a credencial de uma agenda (Google/Outlook) ou API genérica pra
      dar mais contexto ao LLM. Só armazena por enquanto.
    </p>

    <form v-if="showForm" class="flex flex-col gap-3 rounded-lg border p-3" @submit.prevent="save">
      <div class="flex flex-col gap-1.5">
        <Label for="int_name">Nome</Label>
        <Input id="int_name" v-model="name" required maxlength="255" placeholder="Agenda principal" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="int_type">Tipo</Label>
        <select id="int_type" v-model="type" :class="SELECT_CLASS">
          <option value="google_calendar">Google Calendar</option>
          <option value="outlook_calendar">Calendário Outlook</option>
          <option value="generic">Genérica (host + chave)</option>
        </select>
      </div>
      <div v-if="type === 'generic'" class="flex flex-col gap-1.5">
        <Label for="int_host">Host</Label>
        <Input id="int_host" v-model="host" placeholder="https://api.exemplo.com" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="int_email">E-mail da conta</Label>
        <Input id="int_email" v-model="email" type="email" placeholder="agenda@empresa.com" />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="int_secret">Senha / API key</Label>
        <Input
          id="int_secret"
          v-model="secret"
          type="password"
          :placeholder="editingId ? 'deixe em branco pra manter a atual' : ''"
        />
      </div>
      <p v-if="formError" class="text-sm text-destructive">{{ formError }}</p>
      <Button type="submit" size="sm" class="w-fit" :disabled="saving">
        {{ saving ? "Salvando..." : "Salvar" }}
      </Button>
    </form>

    <div v-if="integrations?.length" class="flex flex-col divide-y">
      <div
        v-for="integration in integrations"
        :key="integration.id"
        class="flex items-center justify-between gap-3 py-2"
      >
        <div class="flex items-center gap-2 min-w-0">
          <Plug class="size-4 shrink-0 text-muted-foreground" />
          <div class="min-w-0">
            <p class="truncate text-sm font-medium">{{ integration.name }}</p>
            <p class="truncate text-xs text-muted-foreground">
              {{ TYPE_LABELS[integration.type] }}
              <span v-if="integration.email">· {{ integration.email }}</span>
              <span v-if="integration.has_secret">· credencial salva</span>
            </p>
          </div>
        </div>
        <div class="flex shrink-0 gap-1">
          <Button variant="ghost" size="sm" @click="startEdit(integration)">
            Editar
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            class="text-destructive hover:bg-destructive/10 hover:text-destructive"
            :disabled="removingId === integration.id"
            @click="askRemove(integration)"
          >
            <Loader2 v-if="removingId === integration.id" class="size-4 animate-spin" />
            <Trash2 v-else class="size-4" />
          </Button>
        </div>
      </div>
    </div>
    <p v-else class="text-sm text-muted-foreground">Nenhuma integração cadastrada.</p>

    <ConfirmDeleteDialog
      v-model:open="dialogOpen"
      title="Remover integração?"
      :subject="pendingDelete?.name"
      :loading="removingId !== null"
      @confirm="confirmRemove"
    >
      A credencial salva é apagada e não pode ser recuperada.
    </ConfirmDeleteDialog>
  </div>
</template>
