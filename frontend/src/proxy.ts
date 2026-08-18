import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Must match SESSION_COOKIE in src/lib/api.ts */
const SESSION_COOKIE = "as_logged_in";

function isProtectedPath(pathname: string): boolean {
  const prefixes = [
    "/dashboard",
    "/classroom",
    "/my-courses",
    "/explore",
    "/certificates",
    "/profile",
    "/settings",
    "/admin",
    "/staff",
    "/checkout",
  ];

  if (prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) {
    return true;
  }

  // Lesson player & quizzes (public catalog remains /courses and /courses/[slug])
  if (/^\/courses\/[^/]+\/learn(\/|$)/.test(pathname)) return true;
  if (/^\/courses\/[^/]+\/quiz(\/|$)/.test(pathname)) return true;

  return false;
}

function safeNextPath(pathname: string, search: string): string {
  const next = `${pathname}${search}`;
  if (!next.startsWith("/") || next.startsWith("//")) return "/dashboard";
  return next;
}

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  const loggedIn = request.cookies.get(SESSION_COOKIE)?.value === "1";
  if (loggedIn) {
    return NextResponse.next();
  }

  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.search = "";
  loginUrl.searchParams.set("next", safeNextPath(pathname, search));
  return NextResponse.redirect(loginUrl);
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
