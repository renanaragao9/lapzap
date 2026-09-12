<script setup lang="ts">
definePageMeta({ layout: "blank" });

const api = useApi();

const name = ref("");
const businessType = ref("barbearia");
const phoneNumber = ref("");
const plan = ref("starter");
const error = ref("");
const loading = ref(false);
const done = ref(false);

const SELECT_CLASS =
  "dark:bg-input/30 border-input focus-visible:border-ring focus-visible:ring-ring/50 h-8 rounded-lg border bg-transparent px-2.5 py-1 text-base transition-colors focus-visible:ring-3 md:text-sm w-full min-w-0 outline-none";

async function handleSubmit() {
  error.value = "";
  if (!phoneNumber.value) {
    error.value = "Informe o DDD e os 9 dígitos do número.";
    return;
  }
  loading.value = true;
  try {
    await api("/businesses/signup", {
      method: "POST",
      body: {
        name: name.value,
        business_type: businessType.value,
        contact_phone_number: phoneNumber.value,
        plan: plan.value,
      },
    });
    done.value = true;
  } catch (err: any) {
    error.value = err?.data?.detail ?? "Não foi possível enviar o cadastro.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="dark relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6"
  >
    <div
      class="absolute inset-0 [background-image:radial-gradient(var(--color-white)_1px,transparent_1px)]/8 bg-size-[24px_24px]"
    />
    <div
      class="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-primary/20 blur-3xl"
    />
    <div
      class="absolute -right-32 -bottom-32 h-96 w-96 rounded-full bg-primary/10 blur-3xl"
    />

    <div class="relative flex w-full max-w-sm flex-col items-center gap-6">
      <div class="flex items-center gap-2.5">
        <img
          src="/logo-aragao-labs.jpeg"
          alt="AragaoLabs"
          class="size-9 rounded-lg object-cover"
        />
        <span class="text-lg font-semibold text-foreground">LapZap</span>
      </div>

      <Card
        class="w-full border-white/10 bg-card/60 backdrop-blur-xl supports-backdrop-filter:bg-card/40"
      >
        <template v-if="done">
          <CardHeader>
            <CardTitle>Cadastro recebido</CardTitle>
            <CardDescription>
              Vamos conectar o WhatsApp do seu negócio e entrar em contato em
              breve pra ativar o atendimento.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button as-child class="w-full">
              <NuxtLink to="/login">Voltar pro login</NuxtLink>
            </Button>
          </CardContent>
        </template>

        <template v-else>
          <CardHeader>
            <CardTitle>Cadastre seu negócio</CardTitle>
            <CardDescription>
              Preencha os dados abaixo pra começar a usar o LapZap no seu
              WhatsApp.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
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
                <select
                  id="business_type"
                  v-model="businessType"
                  :class="SELECT_CLASS"
                >
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

              <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
              <Button type="submit" class="mt-2 w-full" :disabled="loading">
                {{ loading ? "Enviando..." : "Cadastrar" }}
              </Button>
            </form>

            <p class="mt-4 text-center text-sm text-muted-foreground">
              Já tem conta?
              <NuxtLink to="/login" class="text-primary hover:underline"
                >Entrar</NuxtLink
              >
            </p>
          </CardContent>
        </template>
      </Card>
    </div>
  </div>
</template>
