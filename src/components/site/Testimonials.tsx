const quotes = [
  { q: "AmpAware paid for itself in the first quarter. The anomaly alerts caught a failing compressor two weeks before it would have tripped our entire line.", n: "Ananya Menon", r: "Plant Engineer, Cochin Refinery" },
  { q: "The KSEB billing engine is uncanny. Our monthly forecast has been within ₹40 of the actual bill for six cycles straight.", n: "Rohit Varghese", r: "Facilities Lead, Infopark" },
  { q: "Finally an energy dashboard that doesn't look like it shipped in 2014.", n: "Lakshmi Iyer", r: "CTO, GreenGrid Labs" },
];

export function Testimonials() {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-7xl px-4">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Trusted by operators</span>
          <h2 className="mt-3 text-4xl font-semibold tracking-tight text-secondary md:text-5xl">Loved by the engineers who run the grid.</h2>
        </div>
        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {quotes.map((q) => (
            <figure key={q.n} className="flex h-full flex-col justify-between rounded-2xl border border-border bg-card p-6 shadow-card-soft">
              <blockquote className="text-sm leading-relaxed text-secondary">"{q.q}"</blockquote>
              <figcaption className="mt-6 flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-primary text-sm font-semibold text-primary-foreground">
                  {q.n.split(" ").map((p) => p[0]).join("")}
                </span>
                <div>
                  <div className="text-sm font-semibold text-secondary">{q.n}</div>
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