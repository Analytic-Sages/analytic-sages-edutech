export const FEATURED_COHORT_SLUG = "cohort-9-blockchain-data";

export function resolvePostLoginPath(role: string | undefined, nextPath: string) {
  const next = nextPath.startsWith("/") && !nextPath.startsWith("//") ? nextPath : "/dashboard";
  if (next !== "/dashboard") {
    return next;
  }
  if (role === "admin") return "/admin";
  if (role === "instructor") return "/staff";
  if (role === "operations") return "/admin/events";
  return next;
}
