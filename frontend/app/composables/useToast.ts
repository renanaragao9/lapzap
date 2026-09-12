interface ToastMessage {
  id: number;
  type: "success" | "error";
  message: string;
}

let nextId = 0;

// ponytail: plain reactive state, no external toast lib — vue-sonner's
// ToastState never reached this app's mounted <Toaster> (reproduced with
// toast() and <Toaster> in the same file, same module instance, still no
// re-render), so a ~30-line home-grown toast is more reliable than chasing
// that bug further.
export function useToasts() {
  return useState<ToastMessage[]>("toasts", () => []);
}

function push(type: ToastMessage["type"], message: string) {
  const toasts = useToasts();
  const id = nextId++;
  toasts.value.push({ id, type, message });
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }, 4000);
}

export const toast = {
  success: (message: string) => push("success", message),
  error: (message: string) => push("error", message),
};
