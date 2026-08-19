import type { ProgramDuneDashboard } from "@/lib/program-pages";

function duneQueryUrl(embedSrc: string) {
  return embedSrc.replace("/embeds/", "/queries/");
}

export function ProgramDuneGrid({ items }: { items: ProgramDuneDashboard[] }) {
  if (items.length === 0) return null;

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      {items.map((item) => (
        <article key={item.id} className="flex flex-col overflow-hidden rounded-xl border bg-card shadow-sm">
          <div className="space-y-1 px-5 pt-5">
            <h3 className="font-heading text-base font-bold leading-snug text-foreground sm:text-lg">
              {item.title}
            </h3>
            {item.description ? (
              <p className="line-clamp-2 text-sm text-muted-foreground">{item.description}</p>
            ) : null}
          </div>
          <div className="relative mx-5 mt-4 aspect-[16/10] overflow-hidden rounded-lg bg-muted">
            <iframe
              src={item.embedSrc}
              title={item.title}
              className="absolute inset-0 size-full border-0"
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>
          <div className="flex items-center justify-between gap-3 px-5 py-4 text-sm">
            <p className="text-muted-foreground">
              @{item.author} <span className="text-muted-foreground/80">with Dune</span>
            </p>
            <a
              href={duneQueryUrl(item.embedSrc)}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-blue-600 underline underline-offset-2 dark:text-blue-400"
            >
              View on Dune
            </a>
          </div>
        </article>
      ))}
    </div>
  );
}
