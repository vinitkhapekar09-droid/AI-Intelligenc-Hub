import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import NewsCard from "../components/NewsCard";

function normalizeItems(payload) {
  const raw = payload?.issue?.items || payload?.items;
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
    issue_date: item.issue_date || payload?.issue?.issue_date || "",
  }));
}

function LandingPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [issue, setIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [subscribeLoading, setSubscribeLoading] = useState(false);
  const [subscribeMessage, setSubscribeMessage] = useState("");
  const [subscribeError, setSubscribeError] = useState("");

  useEffect(() => {
    const fetchDigest = async () => {
      try {
        setLoading(true);
        const { data } = await api.get("/daily-digest");
        setIssue(data?.issue || null);
        setItems(normalizeItems(data).slice(0, 3));
      } catch (e) {
        setError(e?.response?.data?.detail || "Failed to load intelligence feed.");
      } finally {
        setLoading(false);
      }
    };
    fetchDigest();
  }, []);

  const subscribe = async (event) => {
    event.preventDefault();
    setSubscribeError("");
    setSubscribeMessage("");
    if (!email.trim()) {
      setSubscribeError("Please enter a valid email.");
      return;
    }
    try {
      setSubscribeLoading(true);
      const { data } = await api.post("/subscribe", { email: email.trim() });
      setSubscribeMessage(data?.message || "Subscribed successfully.");
      setEmail("");
    } catch (e) {
      setSubscribeError(e?.response?.data?.detail || "Subscription failed.");
    } finally {
      setSubscribeLoading(false);
    }
  };

  return (
    <main>
      <section className="max-w-7xl mx-auto px-6 py-24 md:py-32 flex flex-col items-center text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 bg-secondary-container rounded-full mb-6">
          <span className="font-label-md text-label-md text-on-secondary-container">Daily AI Research Partner</span>
        </div>
        <h1 className="font-h1 text-h1 md:text-5xl md:leading-tight max-w-4xl mb-6 text-on-background">Read the day&apos;s most important AI news, then research it with chat.</h1>
        <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-10">
          AI Intelligence Hub delivers a daily issue of important papers and news, stores it as a searchable archive, and gives members a research workspace to ask follow-ups, compare ideas, and brainstorm from that day&apos;s corpus.
        </p>
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <button onClick={() => navigate("/auth")} className="bg-primary text-on-primary font-button text-button px-8 py-3 rounded hover:opacity-90 transition-all">Join for Free</button>
          <button onClick={() => navigate("/auth")} className="bg-surface-container-lowest text-on-surface border border-outline-variant font-button text-button px-8 py-3 rounded hover:bg-surface-container-low transition-all">Open Chat Workspace</button>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 pb-24">
        <div className="mb-12 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="font-h2 text-h2 text-on-surface">Today&apos;s Digest Preview</h2>
            <div className="h-1 w-12 bg-primary mt-2"></div>
          </div>
          <p className="max-w-xl font-body-md text-body-md text-on-surface-variant">
            Public visitors see the latest stored issue preview. Signed-in readers can browse the full archive feed and continue into the research workspace.
          </p>
        </div>

        {issue ? (
          <div className="mb-8 rounded border border-slate-200 bg-slate-50 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Latest issue</p>
            <h3 className="mt-2 text-xl font-semibold text-slate-900">{issue.title}</h3>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">{issue.summary}</p>
          </div>
        ) : null}

        {loading ? <p className="font-body-md text-body-md text-on-surface-variant">Loading news...</p> : null}
        {error ? <p className="font-body-md text-body-md text-error">{error}</p> : null}
        {!loading && !error && items.length === 0 ? <p className="font-body-md text-body-md text-on-surface-variant">No digest items available yet.</p> : null}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
          {items.map((item) => <NewsCard key={item.id} {...item} />)}
        </div>
      </section>

      <section className="bg-surface-container-low py-xl">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-gutter">
          <div>
            <h2 className="font-h2 text-h2 text-on-surface">Join the morning intelligence.</h2>
            <p className="font-body-md text-body-md text-on-surface-variant">Daily signal in your inbox, plus a workspace to research each issue after it lands.</p>
          </div>
          <form className="w-full md:w-auto flex flex-col sm:flex-row gap-xs" onSubmit={subscribe}>
            <input value={email} onChange={(e) => setEmail(e.target.value)} className="bg-white border border-outline-variant px-4 py-2 w-full md:w-64 rounded focus:ring-2 focus:ring-primary/10 focus:border-primary outline-none transition-all" placeholder="email@address.com" type="email" />
            <button disabled={subscribeLoading} className="bg-primary text-on-primary font-button text-button px-6 py-2 rounded hover:opacity-90 transition-all">
              {subscribeLoading ? "Subscribing..." : "Subscribe"}
            </button>
          </form>
        </div>
        {subscribeMessage ? <p className="max-w-7xl mx-auto px-6 mt-3 text-sm text-emerald-700">{subscribeMessage}</p> : null}
        {subscribeError ? <p className="max-w-7xl mx-auto px-6 mt-3 text-sm text-error">{subscribeError}</p> : null}
      </section>
    </main>
  );
}

export default LandingPage;
