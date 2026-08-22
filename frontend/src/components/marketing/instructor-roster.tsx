type Instructor = {
  id: string;
  name: string;
  title: string;
  photo_url: string | null;
  bullets: string[];
  role_label: string;
};

function initials(name: string) {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || "AS";
}

export function InstructorRoster({ instructors }: { instructors?: Instructor[] | null }) {
  const people = instructors?.filter((item) => item.name.trim()) ?? [];
  if (people.length === 0) return null;

  return (
    <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
      <h2 className="text-center font-heading text-3xl font-bold sm:text-4xl">Who teaches</h2>
      <p className="mt-3 text-center text-muted-foreground">
        The people leading this program.
      </p>
      <div className={`mt-10 grid gap-6 ${people.length > 1 ? "md:grid-cols-2" : "mx-auto max-w-xl"}`}>
        {people.map((person) => (
          <article key={person.id} className="rounded-2xl border bg-card p-6 shadow-card">
            <div className="flex items-start gap-4">
              {person.photo_url ? (
                // External or /public paths; next/image remote hosts are not registered for staff photos.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={person.photo_url}
                  alt={person.name}
                  className="size-16 rounded-full object-cover"
                />
              ) : (
                <div className="flex size-16 shrink-0 items-center justify-center rounded-full bg-brand-navy text-sm font-semibold text-white">
                  {initials(person.name)}
                </div>
              )}
              <div>
                <p className="font-heading text-lg font-semibold">{person.name}</p>
                <p className="text-sm text-brand-orange">{person.role_label || person.title}</p>
                {person.title && person.role_label && person.title !== person.role_label ? (
                  <p className="text-sm text-muted-foreground">{person.title}</p>
                ) : null}
              </div>
            </div>
            {person.bullets.length > 0 ? (
              <ul className="mt-4 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-muted-foreground">
                {person.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
