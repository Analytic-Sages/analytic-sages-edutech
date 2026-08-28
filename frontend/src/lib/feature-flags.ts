/** Public opportunities hub. Off until go-live. Baked in at build — redeploy after changing. */
export function isOpportunitiesPublic() {
  return process.env.NEXT_PUBLIC_OPPORTUNITIES_PUBLIC === "true";
}
