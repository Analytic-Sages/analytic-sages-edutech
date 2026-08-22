import { NextResponse } from "next/server";

/**
 * Do not gate protected pages on the JS `as_logged_in` cookie.
 * That flag can be missing after a refresh even when the httpOnly refresh
 * token is valid. RequireAuth restores the session from `/api/v1/auth/refresh`.
 */
export function proxy() {
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/classroom",
    "/classroom/:path*",
    "/my-courses/:path*",
    "/explore/:path*",
    "/certificates/:path*",
    "/profile/:path*",
    "/settings/:path*",
    "/admin",
    "/admin/:path*",
    "/staff",
    "/staff/:path*",
    "/checkout/:path*",
    "/courses/:slug/learn/:path*",
    "/courses/:slug/quiz/:path*",
  ],
};
