import type { Business } from "~/types/business";

// Cached by the "my-businesses" key: calling this from the layout, a page's
// middleware and the page itself in the same navigation only hits the API once.
export function useMyBusiness() {
  const api = useApi();
  return useAsyncData("my-businesses", () => api<Business[]>("/businesses/mine"));
}
