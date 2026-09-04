"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Award,
  BarChart3,
  BookOpen,
  Briefcase,
  CalendarDays,
  CreditCard,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Moon,
  Radio,
  Settings,
  Sun,
  Users,
  PenLine,
  Share2,
  type LucideIcon,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { AppSearch } from "@/components/layout/app-search";
import { useTheme } from "@/components/providers/theme-provider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import type { NavItem, NavItemId } from "@/config/navigation";
import { getMe, logout, type AuthUser } from "@/lib/api";
import { initialsFor } from "@/lib/user-display";
import { cn } from "@/lib/utils";

const navIcons: Record<NavItemId, LucideIcon> = {
  dashboard: LayoutDashboard,
  classroom: Radio,
  courses: BookOpen,
  events: CalendarDays,
  opportunities: Briefcase,
  explore: GraduationCap,
  certificates: Award,
  users: Users,
  payments: CreditCard,
  analytics: BarChart3,
  settings: Settings,
  insights: PenLine,
  referrals: Share2,
};

type AppSidebarProps = {
  nav: NavItem[];
};

export function AppSidebar({ nav }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-sidebar lg:block">
      <div className="flex h-16 items-center border-b px-6">
        <Logo size="sm" />
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {nav.map((item) => {
          const Icon = navIcons[item.icon];
          const active =
            pathname === item.href ||
            (item.href !== "/admin" && pathname.startsWith(`${item.href}/`));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-brand-navy text-white dark:bg-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="size-4 shrink-0" />
              {item.title}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export function MobileNav({ nav }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <Sheet>
      <SheetTrigger
        render={<Button variant="ghost" size="icon" className="lg:hidden" />}
      >
        <Menu className="size-5" />
      </SheetTrigger>
      <SheetContent side="left" className="w-72 p-0">
        <div className="flex h-16 items-center border-b px-6">
          <Logo size="sm" />
        </div>
        <nav className="flex flex-col gap-1 p-4">
          {nav.map((item) => {
            const Icon = navIcons[item.icon];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                  active ? "bg-brand-navy text-white dark:bg-primary" : "text-muted-foreground"
                )}
              >
                <Icon className="size-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}

export function AppTopbar({ nav }: { nav: NavItem[] }) {
  const { toggleTheme } = useTheme();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleLogout() {
    await logout();
    router.push("/login");
    router.refresh();
  }

  const initials = user ? initialsFor(user.full_name, user.email) : "-";

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur sm:px-6">
      <MobileNav nav={nav} />
      <Logo size="sm" className="lg:hidden" />
      <AppSearch />
      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          <Moon className="size-4 dark:hidden" />
          <Sun className="hidden size-4 dark:block" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button variant="ghost" className="relative size-8 rounded-full p-0" />
            }
          >
            <Avatar className="size-8">
              <AvatarFallback className="bg-brand-navy text-xs text-white">{initials}</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {user && (
              <div className="px-2 py-1.5">
                <p className="truncate text-sm font-medium">{user.full_name || user.email}</p>
                <p className="truncate text-xs text-muted-foreground">{user.email}</p>
              </div>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem className="p-0">
              <Link href="/profile" className="flex w-full items-center px-1.5 py-1">
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem className="p-0">
              <Link href="/settings" className="flex w-full items-center px-1.5 py-1">
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="p-0">
              <button
                type="button"
                onClick={handleLogout}
                className="flex w-full items-center px-1.5 py-1 text-left"
              >
                Log out
              </button>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export function AppShell({
  nav,
  children,
}: {
  nav: NavItem[];
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar nav={nav} />
      <div className="flex flex-1 flex-col">
        <AppTopbar nav={nav} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
