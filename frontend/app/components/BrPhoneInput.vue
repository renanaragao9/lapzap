<script setup lang="ts">
// Masked BR mobile phone input. v-model is the E.164 string (+55DDNNNNNNNNN)
// when complete, "" while incomplete — parent just checks truthiness.
const props = defineProps<{
  modelValue?: string;
  id?: string;
}>();
const emit = defineEmits<{
  "update:modelValue": [string];
}>();

// ponytail: assumes Brazilian mobile numbers (+55, 11 digits) — this app's
// only real use case. Upgrade to libphonenumber if other countries show up.
function digitsFromE164(value?: string): string {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  return digits.length > 11 && digits.startsWith("55")
    ? digits.slice(2)
    : digits;
}

function formatBrPhone(digits: string): string {
  if (!digits) return "";
  let out = `(${digits.slice(0, 2)}`;
  if (digits.length >= 2) out += ") ";
  out += digits.slice(2, 3);
  if (digits.length > 3) out += `-${digits.slice(3, 7)}`;
  if (digits.length > 7) out += `-${digits.slice(7, 11)}`;
  return out;
}

const digits = ref(digitsFromE164(props.modelValue));
const display = computed<string>({
  get: () => formatBrPhone(digits.value),
  set: (value) => {
    digits.value = value.replace(/\D/g, "").slice(0, 11);
    emit(
      "update:modelValue",
      digits.value.length === 11 ? `+55${digits.value}` : "",
    );
  },
});

// Blocks a non-digit keystroke before it lands in the DOM. Filtering only
// via the v-model round-trip (above) lags a tick behind on fast typing,
// letting letters flash through until the next correction catches up.
function blockNonDigitKeystroke(e: InputEvent) {
  if (e.inputType === "insertText" && e.data && /\D/.test(e.data)) {
    e.preventDefault();
  }
}
</script>

<template>
  <Input
    :id="id"
    v-model="display"
    required
    inputmode="numeric"
    placeholder="(85) 9-9999-9999"
    maxlength="16"
    @beforeinput="blockNonDigitKeystroke"
  />
</template>
