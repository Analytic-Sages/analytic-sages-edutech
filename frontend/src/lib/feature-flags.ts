/** Public opportunities hub. Off until go-live. Baked in at build — redeploy after changing. */
export function isOpportunitiesPublic() {
  return process.env.NEXT_PUBLIC_OPPORTUNITIES_PUBLIC === "true";
}

/** Public Referral Partner programme pages. Off until go-live — admins can still preview. */
export function isPartnersPublic() {
  return process.env.NEXT_PUBLIC_PARTNERS_PUBLIC === "true";
}
