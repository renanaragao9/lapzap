<script setup lang="ts">
import { Building2, Loader2 } from "lucide-vue-next";
import type { Business } from "~/types/business";

definePageMeta({ middleware: "admin-only" });

const BUSINESS_TYPE_LABELS: Record<string, string> = {
  barbearia: "Barbearia",
  loja: "Loja",
  generico: "Outro",
};

const SELECT_CLASS =
  "dark:bg-input/30 border-input focus-visible:border-ring focus-visible:ring-ring/50 h-8 rounded-lg border bg-transparent px-2.5 py-1 text-base transition-colors focus-visible:ring-3 md:text-sm w-full min-w-0 outline-none";

const api = useApi();
const {
  data: businesses,
  pending,
  error,
} = await useAsyncData("businesses", () => api<Business[]>("/businesses"));

const showCreate = ref(false);
const name = ref("");
const businessType = ref("barbearia");
const phoneNumber = ref("");
const plan = ref("starter");
const email = ref("");
const password = ref("");
const createError = ref("");
const creating = ref(false);

async function createBusiness() {
  createError.value = "";
  if (!phoneNumber.value) {
    createError.value = "Informe o DDD e os 9 dígitos do número.";
    return;
  }
  creating.value = true;
  try {
    await api("/businesses/signup", {
      method: "POST",
      body: {
        name: name.value,
        business_type: businessType.value,
        contact_phone_number: phoneNumber.value,
        plan: plan.value,
        email: email.value,
        password: password.value,
      },
    });
    name.value = "";
    phoneNumber.value = "";
    email.value = "";
    password.value = "";
    showCreate.value = false;
    await refreshNuxtData("businesses");
    toast.success("Negócio criado.");
  } catch (err: any) {
    createError.value = err?.data?.detail ?? "Não foi possível criar o negócio.";
  } finally {
    creating.value = false;
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">Negócios</h1>
        <p class="text-sm text-muted-foreground">
          {{
            businesses?.length
              ? `${businesses.length} negócio${businesses.length > 1 ? "s" : ""} cadastrado${businesses.length > 1 ? "s" : ""}`
              : "Cadastros públicos aguardando ativação da instância WhatsApp"
          }}
        </p>
      </div>
      <Button size="sm" @click="showCreate = !showCreate">
        {{ showCreate ? "Cancelar" : "Criar negócio" }}
      </Button>
    </div>

    <Card v-if="showCreate" class="p-6">
      <form class="flex flex-col gap-4" @submit.prevent="createBusiness">
        <div class="flex flex-col gap-1.5">
          <Label for="name">Nome do negócio</Label>
          <Input
            id="name"
            v-model="name"
            required
            maxlength="255"
            placeholder="Barbearia do Zé"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="business_type">Tipo de negócio</Label>
          <select id="business_type" v-model="businessType" :class="SELECT_CLASS">
            <option value="barbearia">Barbearia</option>
            <option value="loja">Loja</option>
            <option value="generico">Outro</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="phone_number">Número de contato (WhatsApp)</Label>
          <BrPhoneInput id="phone_number" v-model="phoneNumber" />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="plan">Plano</Label>
          <select id="plan" v-model="plan" :class="SELECT_CLASS">
            <option value="starter">Starter</option>
            <option value="pro">Pro</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="email">E-mail de acesso</Label>
          <Input id="email" v-model="email" type="email" required placeholder="dono@negocio.com" />
        </div>

        <div class="flex flex-col gap-1.5">
          <Label for="password">Senha</Label>
          <Input
            id="password"
            v-model="password"
            type="password"
            required
            minlength="6"
            placeholder="mínimo 6 caracteres"
          />
        </div>

        <p v-if="createError" class="text-sm text-destructive">{{ createError }}</p>
        <Button type="submit" class="w-fit" :disabled="creating">
          {{ creating ? "Criando..." : "Criar" }}
        </Button>
      </form>
    </Card>

    <Card class="overflow-hidden py-0">
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <p v-else-if="error" class="p-6 text-sm text-destructive">
        Não foi possível carregar os negócios.
      </p>

      <template v-else-if="businesses?.length">
        <div class="hidden sm:block">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Contato</TableHead>
                <TableHead>Plano</TableHead>
                <TableHead>Status</TableHead>
                <TableHead class="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="b in businesses" :key="b.id">
                <TableCell class="font-medium">{{ b.name }}</TableCell>
                <TableCell class="text-muted-foreground">{{
                  BUSINESS_TYPE_LABELS[b.business_type] ?? b.business_type
                }}</TableCell>
                <TableCell class="font-mono text-muted-foreground">{{
                  b.contact_phone_number
                }}</TableCell>
                <TableCell class="text-muted-foreground">{{
                  b.plan
                }}</TableCell>
                <TableCell>
                  <Badge :variant="b.status === 'active' ? 'default' : 'outline'">
                    {{ b.status === "active" ? "Ativo" : "Pendente" }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div class="flex justify-end">
                    <Button as-child variant="outline" size="sm">
                      <NuxtLink :to="`/negocios/${b.id}`">
                        {{ b.status === "active" ? "Editar" : "Ativar" }}
                      </NuxtLink>
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div class="divide-y sm:hidden">
          <div
            v-for="b in businesses"
            :key="b.id"
            class="flex items-center justify-between gap-3 p-4"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <p class="truncate font-medium">{{ b.name }}</p>
                <Badge :variant="b.status === 'active' ? 'default' : 'outline'">
                  {{ b.status === "active" ? "Ativo" : "Pendente" }}
                </Badge>
              </div>
              <p class="mt-0.5 truncate text-sm text-muted-foreground">
                {{ BUSINESS_TYPE_LABELS[b.business_type] ?? b.business_type }} ·
                {{ b.contact_phone_number }}
              </p>
            </div>
            <Button as-child variant="outline" size="sm">
              <NuxtLink :to="`/negocios/${b.id}`">
                {{ b.status === "active" ? "Editar" : "Ativar" }}
              </NuxtLink>
            </Button>
          </div>
        </div>
      </template>

      <div v-else class="flex flex-col items-center gap-3 py-16 text-center">
        <div
          class="flex size-10 items-center justify-center rounded-full bg-muted"
        >
          <Building2 class="size-5 text-muted-foreground" />
        </div>
        <div>
          <p class="text-sm font-medium">Nenhum negócio cadastrado</p>
          <p class="text-sm text-muted-foreground">
            Cadastros novos aparecem aqui assim que alguém preencher o
            formulário público.
          </p>
        </div>
      </div>
    </Card>
  </div>
</template>
