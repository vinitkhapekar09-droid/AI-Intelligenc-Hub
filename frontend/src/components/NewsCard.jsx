function formatDateLabel(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function NewsCard({ title, summary, why_it_matters, source, doc_type, url, timestamp, issue_date }) {
  const isResearch = String(doc_type || "news").toLowerCase() === "research";
  return (
    <article className="bg-white border border-slate-200 p-6 flex flex-col justify-between hover:border-blue-200 transition-colors">
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <span className={`font-label-md text-label-md uppercase tracking-widest ${isResearch ? "text-blue-600" : "text-emerald-600"}`}>
            {isResearch ? "Research" : "News"}
          </span>
          <span className="text-outline text-[10px]">•</span>
          <span className="font-label-md text-label-md text-outline">{source || "Unknown"}</span>
          {timestamp ? (
            <>
              <span className="text-outline text-[10px]">•</span>
              <span className="font-label-md text-label-md text-outline">{formatDateLabel(timestamp)}</span>
            </>
          ) : issue_date ? (
            <>
              <span className="text-outline text-[10px]">•</span>
              <span className="font-label-md text-label-md text-outline">{formatDateLabel(issue_date)}</span>
            </>
          ) : null}
        </div>
        <h3 className="font-h3 text-h3 text-on-surface mb-2">{title}</h3>
        <p className="font-body-md text-body-md text-on-surface-variant">{summary || ""}</p>
        {why_it_matters ? (
          <p className="mt-3 rounded bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <span className="font-medium text-slate-900">Why it matters:</span> {why_it_matters}
          </p>
        ) : null}
      </div>
      {url ? (
        <div className="mt-auto pt-4 border-t border-slate-100 flex justify-between items-center">
          <span className="text-outline text-[12px]">Read article</span>
          <a aria-label={`Open article: ${title}`} href={url} target="_blank" rel="noreferrer" className="material-symbols-outlined text-outline text-sm">open_in_new</a>
        </div>
      ) : null}
    </article>
  );
}

export default NewsCard;
