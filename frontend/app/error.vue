<script setup lang="ts">
import { Home, SearchX } from "lucide-vue-next";
import type { NuxtError } from "#app";

const props = defineProps<{
  error: NuxtError;
}>();

const route = useRoute();
const isNotFound = props.error.statusCode === 404;
</script>

<template>
  <div
    class="flex min-h-screen flex-col items-center justify-center gap-8 p-6"
  >
    <Card class="w-full max-w-md">
      <CardContent class="flex flex-col items-center gap-4 py-10 text-center">
        <div
          class="flex size-16 items-center justify-center rounded-full bg-muted"
        >
          <SearchX class="size-8 text-muted-foreground" />
        </div>
        <div>
          <p class="text-2xl font-semibold">
            {{ isNotFound ? "Página não encontrada" : "Algo deu errado" }}
          </p>
          <p class="mt-2 text-base text-muted-foreground">
            {{
              isNotFound
                ? `A página "${route.fullPath}" não existe.`
                : (error.statusMessage ?? "Tente novamente em instantes.")
            }}
          </p>
        </div>
        <Button as-child size="lg" class="mt-2 w-full text-base">
          <NuxtLink to="/">
            <Home class="size-5" />
            Voltar
          </NuxtLink>
        </Button>
      </CardContent>
    </Card>
  </div>
</template>
