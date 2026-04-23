function NewsCard({ title, summary, source, doc_type, url, timestamp }) {
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
              <span className="font-label-md text-label-md text-outline">{timestamp}</span>
            </>
          ) : null}
        </div>
        <h3 className="font-h3 text-h3 text-on-surface mb-2">{title}</h3>
        <p className="font-body-md text-body-md text-on-surface-variant">{summary || ""}</p>
      </div>
      {url ? (
        <div className="mt-auto pt-4 border-t border-slate-100 flex justify-between items-center">
          <span className="text-outline text-[12px]">Open source</span>
          <a href={url} target="_blank" rel="noreferrer" className="material-symbols-outlined text-outline text-sm">open_in_new</a>
        </div>
      ) : null}
    </article>
  );
}

export default NewsCard;
