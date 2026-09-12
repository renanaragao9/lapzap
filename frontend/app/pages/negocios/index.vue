<script setup lang="ts">
import { Building2, Loader2 } from "lucide-vue-next";
import type { Business } from "~/types/business";

definePageMeta({ middleware: "admin-only" });

const BUSINESS_TYPE_LABELS: Record<string, string> = {
  barbearia: "Barbearia",
  loja: "Loja",
  generico: "Outro",
};

const api = useApi();
const {
  data: businesses,
  pending,
  error,
} = await useAsyncData("businesses", () => api<Business[]>("/businesses"));
</script>

<template>
  <div class="flex flex-col gap-6">
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
