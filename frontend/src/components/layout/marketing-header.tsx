"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Moon, Sun } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { useTheme } from "@/components/providers/theme-provider";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { marketingNav } from "@/config/navigation";
import { useIsSignedIn } from "@/hooks/use-access-token";
import { cn } from "@/lib/utils";

export function MarketingHeader() {
  const pathname = usePathname();
  const { toggleTheme } = useTheme();
  const signedIn = useIsSignedIn();

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex h-20 max-w-screen-2xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-10">
        <div className="flex shrink-0 items-center">
          <Logo size="xl" />
        </div>

        <nav className="hidden items-center gap-10 lg:pointer-fine:flex">
          {marketingNav.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative py-1 text-base font-medium transition-colors hover:text-brand-navy dark:hover:text-brand-orange",
                  "after:absolute after:-bottom-1 after:left-0 after:h-0.5 after:w-full after:origin-left after:scale-x-0 after:rounded-full after:bg-brand-orange after:transition-transform after:duration-300 after:ease-out hover:after:scale-x-100",
                  active
                    ? "text-brand-navy after:scale-x-100 dark:text-brand-orange"
                    : "text-muted-foreground"
                )}
              >
                {item.title}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 sm:gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="shrink-0"
          >
            {/* CSS-driven so SSR output matches the client regardless of stored theme */}
            <Moon className="size-4 dark:hidden" />
            <Sun className="hidden size-4 dark:block" />
          </Button>

          <div className="hidden items-center gap-4 lg:pointer-fine:flex">
            {signedIn ? (
              <>
                <ButtonLink
                  href="/my-courses"
                  variant="ghost"
                  className="text-base transition-all hover:-translate-y-0.5"
                >
                  My Courses
                </ButtonLink>
                <ButtonLink
                  href="/dashboard"
                  className="h-11 px-6 text-base bg-brand-orange text-white shadow-card transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-elevated"
                >
                  Dashboard
                </ButtonLink>
              </>
            ) : (
              <>
                <ButtonLink
                  href="/login"
                  variant="ghost"
                  className="text-base transition-all hover:-translate-y-0.5"
                >
                  Log in
                </ButtonLink>
                <ButtonLink
                  href="/register"
                  className="h-11 px-6 text-base bg-brand-orange text-white shadow-card transition-all hover:-translate-y-0.5 hover:bg-brand-orange/90 hover:shadow-elevated"
                >
                  Get Started
                </ButtonLink>
              </>
            )}
          </div>

          <Sheet>
            <SheetTrigger
              className={cn(
                "inline-flex size-10 items-center justify-center rounded-lg lg:pointer-fine:hidden",
                "hover:bg-muted hover:text-foreground"
              )}
            >
              <Menu className="size-6" />
              <span className="sr-only">Open menu</span>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <Logo size="lg" className="mb-2" />
              <nav className="mt-6 flex flex-col gap-5">
                {marketingNav.map((item) => {
                  const active =
                    pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "text-lg font-medium",
                      active ? "text-brand-navy dark:text-brand-orange" : "text-foreground"
                    )}
                  >
                    {item.title}
                  </Link>
                  );
                })}
                <hr className="my-2" />
                {signedIn ? (
                  <>
                    <Link href="/my-courses" className="text-lg font-medium">
                      My Courses
                    </Link>
                    <ButtonLink
                      href="/dashboard"
                      className="h-11 bg-brand-orange text-base text-white hover:bg-brand-orange/90"
                    >
                      Dashboard
                    </ButtonLink>
                  </>
                ) : (
                  <>
                    <Link href="/login" className="text-lg font-medium">
                      Log in
                    </Link>
                    <ButtonLink
                      href="/register"
                      className="h-11 bg-brand-orange text-base text-white hover:bg-brand-orange/90"
                    >
                      Get Started
                    </ButtonLink>
                  </>
                )}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
