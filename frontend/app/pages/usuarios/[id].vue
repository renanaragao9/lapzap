<script setup lang="ts">
import { ArrowLeft, Loader2, PencilLine, SearchX } from "lucide-vue-next";
import type { AppUser } from "~/types/user";

definePageMeta({ middleware: "admin-only" });

const route = useRoute();
const api = useApi();
const id = route.params.id as string;

const {
  data: user,
  pending,
  error,
} = await useAsyncData(`user-${id}`, () => api<AppUser>(`/users/${id}`));

async function update(payload: {
  name: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}) {
  await api(`/users/${id}`, { method: "PUT", body: payload });
  toast.success("Usuário atualizado.");
  await navigateTo("/usuarios");
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col gap-4">
    <NuxtLink
      to="/usuarios"
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
        <CardContent
          class="flex flex-col items-center gap-3 py-10 text-center"
        >
          <div
            class="flex size-10 items-center justify-center rounded-full bg-muted"
          >
            <SearchX class="size-5 text-muted-foreground" />
          </div>
          <p class="text-sm font-medium">Usuário não encontrado</p>
          <Button as-child variant="outline" size="sm">
            <NuxtLink to="/usuarios">Voltar pra lista</NuxtLink>
          </Button>
        </CardContent>
      </template>

      <template v-else-if="user">
        <CardHeader class="flex-row items-center gap-3 space-y-0">
          <div
            class="flex size-9 items-center justify-center rounded-full bg-muted"
          >
            <PencilLine class="size-4 text-foreground" />
          </div>
          <div>
            <CardTitle>Editar usuário</CardTitle>
            <CardDescription>{{ user.email }}</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <UserForm
            submit-label="Salvar"
            :require-password="false"
            :initial-name="user.name"
            :initial-email="user.email"
            :initial-is-active="user.is_active"
            :initial-is-admin="user.is_admin"
            :on-submit="update"
          />
        </CardContent>
      </template>
    </Card>
  </div>
</template>
