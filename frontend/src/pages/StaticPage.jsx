function StaticPage({ title, description, sections }) {
  return (
    <main className="px-6 py-16">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <header className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600">AI Intelligence Hub</p>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="max-w-2xl text-sm leading-6 text-slate-600">{description}</p>
        </header>

        <div className="space-y-8">
          {sections.map((section) => (
            <section key={section.heading} className="space-y-2">
              <h2 className="text-lg font-semibold text-slate-900">{section.heading}</h2>
              <p className="text-sm leading-6 text-slate-600">{section.body}</p>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}

export default StaticPage;
