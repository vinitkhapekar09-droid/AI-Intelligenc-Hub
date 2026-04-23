import { useMemo, useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";

function sourceText(source) {
  if (!source) return "source";
  if (typeof source === "string") return source;
  return source.title || source.source || "source";
}

function ChatPage() {
  const { token } = useAuth();
  const [question, setQuestion] = useState("");
  const [docType, setDocType] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(true);

  const filters = useMemo(() => [
    { label: "All", value: null },
    { label: "Research", value: "research" },
    { label: "News", value: "news" }
  ], []);

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        setHistoryLoading(true);
        const { data } = await api.get("/chat/history?limit=50");
        if (data?.messages && Array.isArray(data.messages)) {
          setMessages(
            data.messages.map((m) => ({
              role: m.role,
              text: m.text,
              sources: m.sources || [],
              ts: new Date(m.timestamp).toLocaleTimeString()
            }))
          );
        }
      } catch (e) {
        console.error("Failed to load chat history:", e);
      } finally {
        setHistoryLoading(false);
      }
    };

    if (token) {
      loadHistory();
    }
  }, [token]);

  const sendMessage = async (event) => {
    event.preventDefault();
    const q = question.trim();
    if (!q || loading) return;

    setError("");
    setMessages((prev) => [...prev, { role: "user", text: q, ts: new Date().toLocaleTimeString() }]);
    setQuestion("");

    try {
      setLoading(true);
      const { data } = await api.post("/chat", {
        question: q,
        doc_type: docType,
        n_results: 5,
        history: messages.slice(-10) // Send last 10 messages as context
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data?.answer || "",
          sources: Array.isArray(data?.sources) ? data.sources : [],
          ts: new Date().toLocaleTimeString()
        }
      ]);
    } catch (e) {
      setError(e?.response?.data?.detail || "Could not send message.");
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Clear all chat history? This cannot be undone.")) return;
    
    try {
      await api.delete("/chat/history");
      setMessages([]);
    } catch (e) {
      setError("Failed to clear history");
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)]">
      <aside className="hidden md:flex flex-col items-center py-4 space-y-4 w-20 border-r border-slate-200 bg-slate-50">
        <button 
          onClick={() => {
            setMessages([]);
            setQuestion("");
            setError("");
          }}
          className="w-12 h-12 bg-primary text-on-primary rounded-xl flex items-center justify-center mb-6 shadow-sm hover:opacity-90 transition-opacity" 
          title="Start new chat"
        >
          <span className="material-symbols-outlined">add</span>
        </button>
        <div className="flex flex-col items-center space-y-6 w-full">
          <div className="flex flex-col items-center w-full py-3 border-l-4 border-blue-600 bg-blue-50/50 text-blue-600">
            <span className="material-symbols-outlined mb-1" style={{ fontVariationSettings: "'FILL' 1" }}>chat</span>
            <span className="font-['Inter'] text-[10px] uppercase tracking-wider">Messages</span>
          </div>
        </div>
        <button 
          onClick={clearHistory}
          className="mt-auto mb-4 w-12 h-12 bg-red-50 text-red-600 rounded-xl flex items-center justify-center hover:bg-red-100 transition-colors"
          title="Clear chat history"
        >
          <span className="material-symbols-outlined text-sm">delete_sweep</span>
        </button>
      </aside>

      <main className="flex-1 flex flex-col bg-surface overflow-hidden">
        <div className="h-14 border-b border-outline-variant bg-surface-container-lowest px-lg flex items-center justify-between">
          <div className="flex items-center gap-xs">
            <span className="material-symbols-outlined text-primary">auto_awesome</span>
            <h2 className="font-h3 text-h3">Intelligent Assistant</h2>
            <span className="ml-2 text-xs text-slate-500">({messages.length} messages saved)</span>
          </div>
          <div className="flex gap-2">
            {filters.map((f) => (
              <button
                key={f.label}
                onClick={() => setDocType(f.value)}
                className={`px-3 py-1 rounded border text-xs ${docType === f.value ? "bg-blue-600 text-white border-blue-600" : "bg-white text-slate-600 border-slate-200"}`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-gutter space-y-gutter max-w-4xl mx-auto w-full">
          {historyLoading ? (
            <p className="font-body-md text-body-md text-on-surface-variant">Loading chat history...</p>
          ) : messages.length === 0 ? (
            <p className="font-body-md text-body-md text-on-surface-variant">Start by asking a question about AI news or research. Your chats will be saved automatically.</p>
          ) : null}

          {messages.map((m, idx) => (
            <div key={`${m.role}-${idx}`} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} items-start gap-md`}>
              {m.role === "assistant" ? (
                <div className="w-8 h-8 rounded bg-surface-container flex items-center justify-center border border-outline-variant">
                  <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                </div>
              ) : null}

              <div className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"} max-w-[80%]`}>
                <div className={`${m.role === "user" ? "bg-primary text-on-primary rounded-tr-none" : "bg-surface-container-low border border-outline-variant rounded-tl-none"} p-md rounded-xl shadow-sm`}>
                  <p className="font-body-md text-body-md whitespace-pre-wrap">{m.text}</p>
                </div>

                {m.sources?.length ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {m.sources.map((s, i) => (
                      <a key={`${i}-${sourceText(s)}`} href={s.url || "#"} target="_blank" rel="noreferrer" className="px-2 py-1 rounded-full border border-outline-variant text-xs text-primary hover:bg-blue-50">
                        {sourceText(s)}
                      </a>
                    ))}
                  </div>
                ) : null}

                <span className="font-label-md text-label-md text-outline mt-xs">{m.ts}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="p-gutter bg-surface">
          {error ? <p className="mb-2 text-sm text-error">{error}</p> : null}
          <form className="max-w-4xl mx-auto relative" onSubmit={sendMessage}>
            <div className="bg-white border border-outline-variant rounded-full flex items-center px-md py-sm shadow-sm focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/10 transition-all">
              <button type="button" className="text-outline hover:text-primary p-xs">
                <span className="material-symbols-outlined">attach_file</span>
              </button>
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="flex-1 bg-transparent border-none focus:ring-0 font-body-md text-body-md px-md text-on-surface"
                placeholder="Type your message..."
                type="text"
              />
              <button disabled={loading} className="bg-primary text-on-primary w-10 h-10 rounded-full flex items-center justify-center hover:opacity-90 transition-all">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>{loading ? "hourglass_top" : "send"}</span>
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
