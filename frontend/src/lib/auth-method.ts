export type AuthMethod = "google" | "email";

const STORAGE_KEY = "as_last_auth_method";

export function getLastAuthMethod(): AuthMethod | null {
  if (typeof window === "undefined") return null;
  const value = localStorage.getItem(STORAGE_KEY);
  if (value === "google" || value === "email") return value;
  return null;
}

export function setLastAuthMethod(method: AuthMethod) {
  localStorage.setItem(STORAGE_KEY, method);
}
