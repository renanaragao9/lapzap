export function useAuth() {
  // useCookie: SSR-safe token storage, readable in middleware and client.
  const token = useCookie<string | null>('lapzap_token', { default: () => null })

  async function login(email: string, password: string) {
    const { access_token } = await $fetch<{ access_token: string }>(
      '/api/v1/auth/login',
      { method: 'POST', body: { email, password } }
    )
    token.value = access_token
  }

  function logout() {
    token.value = null
  }

  return { token, login, logout }
}
