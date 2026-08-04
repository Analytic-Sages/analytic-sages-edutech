import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { siteConfig } from "@/config/site";
import { marketingNav } from "@/config/navigation";

export function MarketingFooter() {
  return (
    <footer className="border-t bg-brand-surface">
      <div className="mx-auto max-w-screen-2xl px-4 py-12 sm:px-6 lg:px-10">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo size="lg" href="/" />
            <p className="mt-4 max-w-sm text-sm text-muted-foreground">
              {siteConfig.description}
            </p>
            <p className="mt-2 text-sm font-medium text-brand-navy dark:text-brand-orange">
              {siteConfig.tagline}
            </p>
          </div>
          <div>
            <h4 className="font-heading text-sm font-semibold">Platform</h4>
            <ul className="mt-4 space-y-2">
              {marketingNav.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="font-heading text-sm font-semibold">Community</h4>
            <ul className="mt-4 space-y-2">
              <li>
                <a
                  href={siteConfig.links.youtube}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  YouTube
                </a>
              </li>
              <li>
                <a
                  href={siteConfig.links.telegram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Telegram
                </a>
              </li>
              <li>
                <a
                  href={siteConfig.links.discord}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Discord
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t pt-8 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
          </p>
          <div className="flex gap-6">
            <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground">
              Contact
            </Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-foreground">
              Privacy
            </Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-foreground">
              Terms
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
