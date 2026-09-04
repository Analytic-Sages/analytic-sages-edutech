export const FEATURED_COHORT_SLUG = "blockchain-data-engineering";

export function resolvePostLoginPath(role: string | undefined, nextPath: string) {
  const next = nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/dashboard";
  if (next !== "/dashboard") {
    return next;
  }
  if (role === "admin") return "/admin";
  if (role === "editor") return "/admin/insights";
  if (role === "author") return "/studio";
  if (role === "instructor") return "/staff";
  if (role === "operations") return "/admin/events";
  return next;
}
