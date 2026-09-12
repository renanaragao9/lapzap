export default defineNuxtRouteMiddleware(async () => {
  const { data: me } = await useCurrentUser();

  if (!me.value?.is_admin) {
    return navigateTo("/numeros");
  }
});
