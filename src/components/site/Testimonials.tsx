const quotes = [
  { q: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.", n: "Lorem Ipsum", r: "Dolor Sit Amet, Consectetur" },
  { q: "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.", n: "Sit Amet", r: "Adipiscing Elit, Sed Do" },
  { q: "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam eaque ipsa quae ab illo inventore.", n: "Consectetur Adipiscing", r: "Eiusmod Tempor, Incididunt" },
];

export function Testimonials() {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-7xl px-4">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Trusted by operators</span>
          <h2 className="mt-3 text-4xl font-semibold tracking-tight text-foreground md:text-5xl">Loved by the engineers who run the grid.</h2>
        </div>
        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {quotes.map((q) => (
            <figure key={q.n} className="flex h-full flex-col justify-between rounded-2xl border border-border bg-card p-6 shadow-card-soft">
              <blockquote className="text-sm leading-relaxed text-foreground">"{q.q}"</blockquote>
              <figcaption className="mt-6 flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-primary text-sm font-semibold text-primary-foreground">
                  {q.n.split(" ").map((p) => p[0]).join("")}
                </span>
                <div>
                  <div className="text-sm font-semibold text-foreground">{q.n}</div>
                  <div className="text-xs text-muted-foreground">{q.r}</div>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}