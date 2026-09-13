// Só deixa entrar quem tem negócio vinculado à própria conta - evita a tela
// vazia de "Meu Negócio" pra quem ainda não tem tenant.
export default defineNuxtRouteMiddleware(async () => {
  const { data: businesses } = await useMyBusiness();

  if (!businesses.value?.length) {
    return navigateTo("/numeros");
  }
});
