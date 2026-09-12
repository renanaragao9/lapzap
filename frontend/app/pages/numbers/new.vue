<script setup lang="ts">
import { ArrowLeft, Plus } from "lucide-vue-next";

const api = useApi();

async function create(payload: { name: string; phone_number: string }) {
  await api("/numbers", { method: "POST", body: payload });
  await navigateTo("/numbers");
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col gap-4">
    <NuxtLink
      to="/numbers"
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
          <CardTitle>Novo número</CardTitle>
          <CardDescription
            >Autorize um número a enviar mensagens pelo
            WhatsApp.</CardDescription
          >
        </div>
      </CardHeader>
      <CardContent>
        <PhoneNumberForm submit-label="Criar" :on-submit="create" />
      </CardContent>
    </Card>
  </div>
</template>
