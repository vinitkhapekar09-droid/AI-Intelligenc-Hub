import { useEffect, useMemo, useState } from "react";
import NewsCard from "../components/NewsCard";
import api from "../api";

function normalizeItems(payload) {
  const raw = payload?.items;
  if (!Array.isArray(raw)) return [];
  return raw.map((item, idx) => ({
    id: item.id || `${item.url || item.title || "item"}-${idx}`,
    title: item.title || "Untitled",
    summary: item.summary || "",
    source: item.source || "AI Intelligence Hub",
    doc_type: item.doc_type || "news",
    url: item.url || "",
    timestamp: item.timestamp || ""
  }));
}

function DigestPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDigest = async () => {
      try {
        setLoading(true);
        const { data } = await api.get("/daily-digest");
        setItems(normalizeItems(data));
      } catch (e) {
        setError(e?.response?.data?.detail || "Failed to load daily digest.");
      } finally {
        setLoading(false);
      }
    };
    fetchDigest();
  }, []);

  const [lead, ...rest] = useMemo(() => items, [items]);

  return (
    <>
      <div className="flex-1 flex w-full max-w-7xl mx-auto pt-4">
        <aside className="hidden md:flex flex-col items-center py-4 space-y-4 w-20 border-r border-slate-200 bg-slate-50">
          <div className="flex flex-col items-center space-y-6">
            <div className="group flex flex-col items-center p-3 space-y-1 text-slate-400 hover:bg-slate-100 transition-all rounded-lg cursor-pointer">
              <span className="material-symbols-outlined">article</span>
              <span className="font-['Inter'] text-[10px] uppercase tracking-wider">Feed</span>
            </div>
            <div className="group flex flex-col items-center p-3 space-y-1 border-l-4 border-blue-600 bg-blue-50/50 text-blue-600 transition-all rounded-r-lg cursor-pointer">
              <span className="material-symbols-outlined">trending_up</span>
              <span className="font-['Inter'] text-[10px] uppercase tracking-wider">Daily</span>
            </div>
          </div>
        </aside>

        <main className="flex-1 ml-0 md:ml-4 px-6 py-10 max-w-4xl mx-auto">
          <header className="mb-10">
            <h1 className="font-h1 text-h1 text-on-surface mb-2">Daily News Feed</h1>
            <p className="font-body-lg text-body-lg text-outline">Clear, objective reporting for high-density reading.</p>
          </header>

          {loading ? <p className="font-body-md text-body-md text-on-surface-variant">Loading digest...</p> : null}
          {error ? <p className="font-body-md text-body-md text-error">{error}</p> : null}
          {!loading && !error && items.length === 0 ? <p className="font-body-md text-body-md text-on-surface-variant">No digest items available yet.</p> : null}

          <div className="space-y-4">
            {lead ? (
              <article className="bg-white border border-slate-200 p-6 flex flex-col md:flex-row gap-6 hover:border-blue-200 transition-colors group">
                <div className="w-full md:w-1/3 aspect-[4/3] bg-surface-container overflow-hidden rounded">
                  <div className="w-full h-full bg-slate-100" />
                </div>
                <div className="flex-1 flex flex-col justify-center">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`font-label-md text-label-md uppercase tracking-widest ${String(lead.doc_type).toLowerCase() === "research" ? "text-blue-600" : "text-emerald-600"}`}>{lead.doc_type}</span>
                    <span className="text-outline text-[10px]">•</span>
                    <span className="font-label-md text-label-md text-outline">{lead.source}</span>
                  </div>
                  <h2 className="font-h2 text-h2 text-on-surface mb-3 group-hover:text-primary transition-colors">{lead.title}</h2>
                  <p className="font-body-md text-body-md text-on-surface-variant line-clamp-3">{lead.summary}</p>
                </div>
              </article>
            ) : null}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rest.map((item) => <NewsCard key={item.id} {...item} />)}
            </div>
          </div>
        </main>
      </div>

      <footer className="bg-white border-t border-slate-200">
        <div className="flex flex-col md:flex-row justify-between items-center w-full px-6 py-8 mt-auto max-w-7xl mx-auto">
          <div className="mb-4 md:mb-0">
            <span className="font-['Inter'] text-xs font-bold text-slate-900">AI Intelligence Hub</span>
            <span className="font-['Inter'] text-xs text-slate-500 ml-2">© 2024</span>
          </div>
          <div className="flex space-x-6">
            <a className="font-['Inter'] text-xs text-slate-500 hover:text-blue-600 transition-colors" href="#">Privacy Policy</a>
            <a className="font-['Inter'] text-xs text-slate-500 hover:text-blue-600 transition-colors" href="#">Terms of Service</a>
            <a className="font-['Inter'] text-xs text-slate-500 hover:text-blue-600 transition-colors" href="#">Help Center</a>
          </div>
        </div>
      </footer>
    </>
  );
}

export default DigestPage;
