<script setup lang="ts">
import { ArrowLeft, Plus } from "lucide-vue-next";

definePageMeta({ middleware: "admin-only" });

const api = useApi();

async function create(payload: {
  name: string;
  email: string;
  password?: string;
  is_active: boolean;
  is_admin: boolean;
}) {
  await api("/users", { method: "POST", body: payload });
  toast.success("Usuário criado.");
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
      <CardHeader class="flex-row items-center gap-3 space-y-0">
        <div
          class="flex size-9 items-center justify-center rounded-full bg-muted"
        >
          <Plus class="size-4 text-foreground" />
        </div>
        <div>
          <CardTitle>Novo usuário</CardTitle>
          <CardDescription>Cria um acesso ao sistema.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <UserForm
          submit-label="Criar"
          require-password
          :on-submit="create"
        />
      </CardContent>
    </Card>
  </div>
</template>
