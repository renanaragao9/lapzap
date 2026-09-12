export function useApi() {
  const { token, logout } = useAuth()

  const api = $fetch.create({
    baseURL: '/api/v1',
    onRequest({ options }) {
      if (token.value) {
        options.headers.set('Authorization', `Bearer ${token.value}`)
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        logout()
        navigateTo('/login')
      }
    }
  })

  return api
}
