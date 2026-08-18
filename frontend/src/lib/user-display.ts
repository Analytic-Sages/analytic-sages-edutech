export function initialsFor(name: string | null | undefined, email?: string) {
  const source = (name || email || "?").trim();
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return source.slice(0, 2).toUpperCase();
}

export function displayName(name: string | null | undefined, email: string) {
  return name?.trim() || email;
}
