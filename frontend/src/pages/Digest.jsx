import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import NewsCard from "../components/NewsCard";
import api from "../api";

const sidebarItems = [
  { label: "Featured", icon: "trending_up", targetId: "featured-story" },
  { label: "Feed", icon: "article", targetId: "digest-feed" },
];

function normalizeItems(payload) {
  const raw = payload?.items;
  if (!Array.isArray(raw)) return [];
  return raw.map((item, idx) => ({
    id: item.id || `${item.url || item.title || "item"}-${idx}`,
    title: item.title || "Untitled",
    summary: item.summary || "",
    why_it_matters: item.why_it_matters || "",
    source: item.source || "AI Intelligence Hub",
    doc_type: item.doc_type || "news",
    url: item.url || "",
    timestamp: item.timestamp || "",
    issue_date: item.issue_date || "",
  }));
}

function DigestPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedIssueDate = searchParams.get("date") || "";
  const [items, setItems] = useState([]);
  const [issues, setIssues] = useState([]);
  const [issue, setIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDigest = async () => {
      try {
        setLoading(true);
        const issueRequest = selectedIssueDate
          ? api.get(`/issues/${selectedIssueDate}`)
          : api.get("/daily-digest");
        const [{ data: issueData }, { data: issuesData }] = await Promise.all([
          issueRequest,
          api.get("/issues", { params: { limit: 10 } }),
        ]);
        const activeIssue = issueData?.issue || null;
        setIssue(activeIssue);
        setItems(normalizeItems({ items: activeIssue?.items || [] }));
        setIssues(Array.isArray(issuesData?.issues) ? issuesData.issues : []);
      } catch (e) {
        setError(e?.response?.data?.detail || "Failed to load research feed.");
      } finally {
        setLoading(false);
      }
    };
    fetchDigest();
  }, [selectedIssueDate]);

  const [lead, ...rest] = useMemo(() => items, [items]);

  const scrollToSection = (targetId) => {
    document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const selectIssue = (nextIssueDate) => {
    if (nextIssueDate) {
      setSearchParams({ date: nextIssueDate });
      return;
    }
    setSearchParams({});
  };

  const featuredCard = (
    <article
      className={`bg-white border border-slate-200 p-6 flex flex-col md:flex-row gap-6 transition-colors group ${
        lead?.url ? "hover:border-blue-200" : ""
      }`}
      id="featured-story"
    >
      <div className="w-full md:w-1/3 aspect-[4/3] bg-surface-container overflow-hidden rounded">
        <div className="w-full h-full bg-slate-100" />
      </div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex items-center space-x-2 mb-2">
          <span className={`font-label-md text-label-md uppercase tracking-widest ${String(lead?.doc_type).toLowerCase() === "research" ? "text-blue-600" : "text-emerald-600"}`}>{lead?.doc_type}</span>
          <span className="text-outline text-[10px]">•</span>
          <span className="font-label-md text-label-md text-outline">{lead?.source}</span>
        </div>
        <h2 className="font-h2 text-h2 text-on-surface mb-3 group-hover:text-primary transition-colors">{lead?.title}</h2>
        <p className="font-body-md text-body-md text-on-surface-variant line-clamp-3">{lead?.summary}</p>
        {lead?.url ? (
          <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-blue-600">
            Open featured story
            <span className="material-symbols-outlined text-base">open_in_new</span>
          </span>
        ) : null}
      </div>
    </article>
  );

  return (
      <div className="flex-1 flex w-full max-w-7xl mx-auto pt-4">
        <aside className="hidden md:flex flex-col items-center py-4 space-y-4 w-20 border-r border-slate-200 bg-slate-50">
          <div className="flex flex-col items-center space-y-6">
            {sidebarItems.map((item, index) => (
              <button
                key={item.label}
                className={`group flex flex-col items-center rounded-r-lg p-3 space-y-1 transition-all ${
                  index === 0
                    ? "border-l-4 border-blue-600 bg-blue-50/50 text-blue-600"
                    : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                }`}
                onClick={() => scrollToSection(item.targetId)}
                type="button"
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="font-['Inter'] text-[10px] uppercase tracking-wider">{item.label}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="flex-1 ml-0 md:ml-4 px-6 py-10 max-w-4xl mx-auto">
          <header className="mb-10">
            <h1 className="font-h1 text-h1 text-on-surface mb-2">AI Research Feed</h1>
            <p className="font-body-lg text-body-lg text-outline">Browse stored daily issues, scan the day&apos;s signal, and jump into research when something deserves a deeper look.</p>
          </header>

          {issues.length ? (
            <div className="mb-8 flex flex-wrap gap-2">
              <button
                className={`rounded-full border px-3 py-1 text-sm ${selectedIssueDate ? "border-slate-200 text-slate-600" : "border-blue-600 bg-blue-600 text-white"}`}
                onClick={() => selectIssue("")}
                type="button"
              >
                Latest
              </button>
              {issues.map((entry) => (
                <button
                  key={entry.issue_date}
                  className={`rounded-full border px-3 py-1 text-sm ${
                    selectedIssueDate === entry.issue_date
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-slate-200 text-slate-600"
                  }`}
                  onClick={() => selectIssue(entry.issue_date)}
                  type="button"
                >
                  {entry.issue_date}
                </button>
              ))}
            </div>
          ) : null}

          {issue ? (
            <div className="mb-8 rounded border border-slate-200 bg-slate-50 p-6">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{issue.issue_date}</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">{issue.title}</h2>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{issue.summary}</p>
            </div>
          ) : null}

          {loading ? <p className="font-body-md text-body-md text-on-surface-variant">Loading feed...</p> : null}
          {error ? <p className="font-body-md text-body-md text-error">{error}</p> : null}
          {!loading && !error && items.length === 0 ? <p className="font-body-md text-body-md text-on-surface-variant">No issue items are available yet.</p> : null}

          <div className="space-y-4">
            {lead ? (
              lead.url ? (
                <a className="block" href={lead.url} rel="noreferrer" target="_blank">
                  {featuredCard}
                </a>
              ) : featuredCard
            ) : null}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4" id="digest-feed">
              {rest.map((item) => <NewsCard key={item.id} {...item} />)}
            </div>
          </div>
        </main>
      </div>
  );
}

export default DigestPage;
