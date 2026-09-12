<script setup lang="ts">
import { Loader2, Plus, UserRound } from "lucide-vue-next";
import type { AppUser } from "~/types/user";

definePageMeta({ middleware: "admin-only" });

const api = useApi();
const {
  data: users,
  pending,
  refresh,
  error,
} = await useAsyncData("users", () => api<AppUser[]>("/users"));

const removingId = ref<number | null>(null);
const dialogOpen = ref(false);
const pendingDelete = ref<AppUser | null>(null);

function askRemove(u: AppUser) {
  pendingDelete.value = u;
  dialogOpen.value = true;
}

async function confirmRemove(e: Event) {
  e.preventDefault();
  const target = pendingDelete.value;
  if (!target) return;
  removingId.value = target.id;
  try {
    await api(`/users/${target.id}`, { method: "DELETE" });
    dialogOpen.value = false;
    await refresh();
    toast.success("Usuário removido.");
  } catch (err: any) {
    toast.error(err?.data?.detail ?? "Não foi possível remover o usuário.");
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
        <h1 class="text-2xl font-semibold tracking-tight">Usuários</h1>
        <p class="text-sm text-muted-foreground">
          {{
            users?.length
              ? `${users.length} usuário${users.length > 1 ? "s" : ""} cadastrado${users.length > 1 ? "s" : ""}`
              : "Gerencie quem acessa o sistema"
          }}
        </p>
      </div>
      <Button as-child class="w-full sm:w-auto">
        <NuxtLink to="/usuarios/novo">
          <Plus class="size-4" />
          Novo usuário
        </NuxtLink>
      </Button>
    </div>

    <Card class="overflow-hidden py-0">
      <div v-if="pending" class="flex items-center justify-center py-16">
        <Loader2 class="size-5 animate-spin text-muted-foreground" />
      </div>

      <p v-else-if="error" class="p-6 text-sm text-destructive">
        Não foi possível carregar os usuários.
      </p>

      <template v-else-if="users?.length">
        <div class="hidden sm:block">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Status</TableHead>
                <TableHead class="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="u in users" :key="u.id">
                <TableCell class="font-medium">{{ u.name }}</TableCell>
                <TableCell class="text-muted-foreground">{{
                  u.email
                }}</TableCell>
                <TableCell>
                  <div class="flex gap-1.5">
                    <Badge :variant="u.is_active ? 'default' : 'outline'">
                      {{ u.is_active ? "Ativo" : "Inativo" }}
                    </Badge>
                    <Badge v-if="u.is_admin" variant="secondary">Admin</Badge>
                  </div>
                </TableCell>
                <TableCell>
                  <div class="flex justify-end">
                    <RowActions
                      :to="`/usuarios/${u.id}`"
                      :removing="removingId === u.id"
                      @remove="askRemove(u)"
                    />
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div class="divide-y sm:hidden">
          <div
            v-for="u in users"
            :key="u.id"
            class="flex items-center justify-between gap-3 p-4"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <p class="truncate font-medium">{{ u.name }}</p>
                <Badge :variant="u.is_active ? 'default' : 'outline'">
                  {{ u.is_active ? "Ativo" : "Inativo" }}
                </Badge>
                <Badge v-if="u.is_admin" variant="secondary">Admin</Badge>
              </div>
              <p class="mt-0.5 truncate text-sm text-muted-foreground">
                {{ u.email }}
              </p>
            </div>
            <RowActions
              :to="`/usuarios/${u.id}`"
              :removing="removingId === u.id"
              @remove="askRemove(u)"
            />
          </div>
        </div>
      </template>

      <div v-else class="flex flex-col items-center gap-3 py-16 text-center">
        <div
          class="flex size-10 items-center justify-center rounded-full bg-muted"
        >
          <UserRound class="size-5 text-muted-foreground" />
        </div>
        <div>
          <p class="text-sm font-medium">Nenhum usuário cadastrado</p>
          <p class="text-sm text-muted-foreground">
            Crie o primeiro usuário adicional pra dar acesso ao sistema.
          </p>
        </div>
        <Button as-child size="sm" class="mt-1">
          <NuxtLink to="/usuarios/novo">
            <Plus class="size-4" />
            Novo usuário
          </NuxtLink>
        </Button>
      </div>
    </Card>

    <ConfirmDeleteDialog
      v-model:open="dialogOpen"
      title="Remover usuário?"
      :subject="pendingDelete?.name"
      :loading="removingId !== null"
      @confirm="confirmRemove"
    >
      ({{ pendingDelete?.email }}) perde acesso ao sistema. Essa ação não pode
      ser desfeita.
    </ConfirmDeleteDialog>
  </div>
</template>
