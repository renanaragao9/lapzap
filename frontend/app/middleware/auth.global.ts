export default defineNuxtRouteMiddleware((to) => {
  if (to.path === "/login" || to.path === "/cadastro") return;

  const { token } = useAuth();
  if (!token.value) {
    return navigateTo("/login");
  }
});
