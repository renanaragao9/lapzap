<script setup lang="ts">
interface PhoneNumber {
  id: number
  name: string
  phone_number: string
}

const route = useRoute()
const api = useApi()
const id = route.params.id as string

const { data: phoneNumber, error } = await useAsyncData(`number-${id}`, () =>
  api<PhoneNumber>(`/numbers/${id}`)
)

async function update(payload: { name: string; phone_number: string }) {
  await api(`/numbers/${id}`, { method: 'PUT', body: payload })
  await navigateTo('/numbers')
}
</script>

<template>
  <div>
    <h1>Editar número</h1>
    <p v-if="error" class="error">Número não encontrado.</p>
    <PhoneNumberForm
      v-else-if="phoneNumber"
      submit-label="Salvar"
      :initial-name="phoneNumber.name"
      :initial-phone-number="phoneNumber.phone_number"
      :on-submit="update"
    />
  </div>
</template>
