import type { AppUser } from "~/types/user";

// Cached by the "me" key: calling this from the layout and from a page's
// middleware in the same navigation only hits the API once.
export function useCurrentUser() {
  const api = useApi();
  return useAsyncData("me", () => api<AppUser>("/auth/me"));
}
