import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";

const ACTIVE_THREAD_STORAGE_KEY = "activeChatThreadId";

function createThreadId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `thread-${Date.now()}`;
}

function sourceText(source) {
  if (!source) return "source";
  if (typeof source === "string") return source;
  return source.title || source.source || "source";
}

function mapMessage(message, idx = 0) {
  return {
    id: message.id || `${message.role}-${message.timestamp || Date.now()}-${idx}`,
    role: message.role,
    text: message.text,
    sources: message.sources || [],
    ts: new Date(message.timestamp || Date.now()).toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    }),
    status: "sent",
  };
}

function buildResearchScopes(issues) {
  const recentIssueScopes = issues.slice(0, 6).map((issue) => ({
    label: issue.issue_date,
    value: issue.issue_date,
  }));

  return [{ label: "All issues", value: "" }, ...recentIssueScopes];
}

function formatThreadTime(value) {
  if (!value) return "";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  return parsed.toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

function buildDraftThread(activeThreadId, threads, messages) {
  if (!activeThreadId || threads.some((thread) => thread.thread_id === activeThreadId)) {
    return null;
  }

  const firstUserMessage = messages.find((message) => message.role === "user");
  return {
    thread_id: activeThreadId,
    title: firstUserMessage?.text?.slice(0, 60) || "New chat",
    last_message: firstUserMessage?.text || "Start a fresh research thread",
    updated_at: new Date().toISOString(),
    message_count: messages.length,
    isDraft: true,
  };
}

function ChatPage() {
  const { token } = useAuth();
  const [question, setQuestion] = useState("");
  const [docType, setDocType] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [threads, setThreads] = useState([]);
  const [issues, setIssues] = useState([]);
  const [issueDate, setIssueDate] = useState("");
  const [activeThreadId, setActiveThreadId] = useState(() => localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY) || "");
  const messageViewportRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);
  const lastThreadIdRef = useRef("");
  const lastMessageCountRef = useRef(0);

  const filters = useMemo(
    () => [
      { label: "All", value: null },
      { label: "Research", value: "research" },
      { label: "News", value: "news" },
    ],
    [],
  );
  const scopes = useMemo(() => buildResearchScopes(issues), [issues]);
  const draftThread = useMemo(
    () => buildDraftThread(activeThreadId, threads, messages),
    [activeThreadId, messages, threads],
  );
  const visibleThreads = useMemo(
    () => (draftThread ? [draftThread, ...threads] : threads),
    [draftThread, threads],
  );
  const activeThread = useMemo(
    () => visibleThreads.find((thread) => thread.thread_id === activeThreadId) || null,
    [activeThreadId, visibleThreads],
  );

  const scrollToBottom = (behavior = "auto") => {
    const viewport = messageViewportRef.current;
    if (!viewport) {
      return;
    }

    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior,
    });
  };

  const refreshThreads = async (preferredThreadId = "") => {
    try {
      setThreadsLoading(true);
      const { data } = await api.get("/chat/threads", { params: { limit: 40 } });
      const nextThreads = Array.isArray(data?.threads) ? data.threads : [];
      setThreads(nextThreads);

      if (preferredThreadId) {
        setActiveThreadId(preferredThreadId);
      } else if (!activeThreadId) {
        if (nextThreads[0]?.thread_id) {
          setActiveThreadId(nextThreads[0].thread_id);
        } else {
          setActiveThreadId(createThreadId());
        }
      } else if (
        nextThreads.length > 0
        && !nextThreads.some((thread) => thread.thread_id === activeThreadId)
        && messages.length === 0
      ) {
        setActiveThreadId(nextThreads[0].thread_id);
      }
    } catch (threadError) {
      console.error("Failed to load chat threads:", threadError);
    } finally {
      setThreadsLoading(false);
    }
  };

  useEffect(() => {
    const loadIssues = async () => {
      try {
        const { data } = await api.get("/issues", { params: { limit: 7 } });
        const nextIssues = Array.isArray(data?.issues) ? data.issues : [];
        setIssues(nextIssues);
        if (!issueDate && nextIssues[0]?.issue_date) {
          setIssueDate(nextIssues[0].issue_date);
        }
      } catch (issueError) {
        console.error("Failed to load issue list:", issueError);
      }
    };

    if (token) {
      loadIssues();
      refreshThreads();
    }
  }, [token]);

  useEffect(() => {
    if (activeThreadId) {
      localStorage.setItem(ACTIVE_THREAD_STORAGE_KEY, activeThreadId);
      return;
    }
    localStorage.removeItem(ACTIVE_THREAD_STORAGE_KEY);
  }, [activeThreadId]);

  useEffect(() => {
    const loadHistory = async () => {
      if (!token) {
        return;
      }

      if (!activeThreadId) {
        setMessages([]);
        setHistoryLoading(false);
        return;
      }

      if (draftThread?.thread_id === activeThreadId) {
        setHistoryLoading(false);
        return;
      }

      try {
        setHistoryLoading(true);
        const { data } = await api.get("/chat/history", {
          params: {
            limit: 100,
            thread_id: activeThreadId,
          },
        });
        const nextMessages = Array.isArray(data?.messages)
          ? data.messages.map((message, idx) => mapMessage(message, idx))
          : [];
        setMessages(nextMessages);
      } catch (historyError) {
        console.error("Failed to load chat history:", historyError);
        setError("Failed to load the selected conversation.");
      } finally {
        setHistoryLoading(false);
      }
    };

    loadHistory();
  }, [activeThreadId, draftThread, token]);

  const startNewChat = () => {
    setError("");
    setQuestion("");
    setMessages([]);
    setDocType(null);
    shouldAutoScrollRef.current = true;
    setActiveThreadId(createThreadId());
    setHistoryLoading(false);
  };

  const sendMessage = async (event) => {
    event.preventDefault();
    const q = question.trim();
    if (!q || loading) return;

    const threadId = activeThreadId || createThreadId();
    const pendingMessageId = createThreadId();

    if (!activeThreadId) {
      setActiveThreadId(threadId);
    }

    setError("");
    setMessages((prev) => [
      ...prev,
      {
        id: pendingMessageId,
        role: "user",
        text: q,
        ts: new Date().toLocaleTimeString([], {
          hour: "numeric",
          minute: "2-digit",
        }),
        status: "sending",
      },
    ]);
    setQuestion("");

    try {
      setLoading(true);
      const { data } = await api.post("/chat", {
        question: q,
        doc_type: docType,
        n_results: 5,
        thread_id: threadId,
        issue_date: issueDate || undefined,
      });

      const resolvedThreadId = data?.thread_id || threadId;
      setActiveThreadId(resolvedThreadId);
      setMessages((prev) => [
        ...prev.map((message) => (
          message.id === pendingMessageId ? { ...message, status: "sent" } : message
        )),
        {
          id: createThreadId(),
          role: "assistant",
          text: data?.answer || "",
          sources: Array.isArray(data?.sources) ? data.sources : [],
          ts: new Date().toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
          }),
          status: "sent",
        },
      ]);
      await refreshThreads(resolvedThreadId);
    } catch (sendError) {
      setMessages((prev) => prev.map((message) => (
        message.id === pendingMessageId ? { ...message, status: "failed" } : message
      )));
      setError(sendError?.response?.data?.detail || "Could not send message.");
    } finally {
      setLoading(false);
    }
  };

  const selectThread = (threadId) => {
    setError("");
    setQuestion("");
    shouldAutoScrollRef.current = true;
    setActiveThreadId(threadId);
  };

  useEffect(() => {
    const viewport = messageViewportRef.current;
    if (!viewport) {
      return;
    }

    const handleScroll = () => {
      const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      shouldAutoScrollRef.current = distanceFromBottom <= 80;
    };

    handleScroll();
    viewport.addEventListener("scroll", handleScroll);
    return () => viewport.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (historyLoading) {
      return;
    }

    const messageCount = messages.length;
    const threadChanged = lastThreadIdRef.current !== activeThreadId;
    const hasNewMessages = messageCount > lastMessageCountRef.current;
    const shouldScroll = shouldAutoScrollRef.current || threadChanged;

    if (shouldScroll) {
      scrollToBottom(threadChanged ? "auto" : (hasNewMessages ? "smooth" : "auto"));
    }

    lastMessageCountRef.current = messageCount;
    lastThreadIdRef.current = activeThreadId;
  }, [activeThreadId, historyLoading, messages]);

  const deleteThread = async (threadId) => {
    try {
      await api.delete(`/chat/threads/${threadId}`);
      const remainingThreads = threads.filter((thread) => thread.thread_id !== threadId);
      setThreads(remainingThreads);

      if (activeThreadId === threadId) {
        if (remainingThreads[0]?.thread_id) {
          setActiveThreadId(remainingThreads[0].thread_id);
        } else {
          startNewChat();
        }
      }
    } catch (deleteError) {
      setError(deleteError?.response?.data?.detail || "Failed to delete chat thread.");
    }
  };

  const clearHistory = async () => {
    if (!window.confirm("Clear all chat history? This cannot be undone.")) return;

    try {
      await api.delete("/chat/history");
      setThreads([]);
      startNewChat();
    } catch (_clearError) {
      setError("Failed to clear history.");
    }
  };

  return (
    <div className="flex h-full min-h-0 overflow-hidden bg-slate-50">
      <aside className="flex w-full max-w-[320px] min-h-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 p-4">
          <button
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-medium text-white hover:opacity-90"
            onClick={startNewChat}
            type="button"
          >
            <span className="material-symbols-outlined text-lg">add</span>
            New chat
          </button>
        </div>

        <div className="border-b border-slate-200 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Saved conversations</p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
          {threadsLoading ? (
            <p className="px-2 text-sm text-slate-500">Loading conversations...</p>
          ) : visibleThreads.length === 0 ? (
            <p className="px-2 text-sm text-slate-500">No saved chats yet. Start the first one.</p>
          ) : (
            <div className="space-y-2">
              {visibleThreads.map((thread) => (
                <button
                  key={thread.thread_id}
                  className={`group flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition-colors ${
                    activeThreadId === thread.thread_id
                      ? "border-blue-200 bg-blue-50"
                      : "border-transparent bg-slate-50 hover:border-slate-200 hover:bg-white"
                  }`}
                  onClick={() => selectThread(thread.thread_id)}
                  type="button"
                >
                  <span className="material-symbols-outlined mt-0.5 text-[18px] text-slate-400">
                    {thread.isDraft ? "edit_square" : "chat"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {thread.title || "New chat"}
                      </p>
                      <span className="shrink-0 text-[11px] text-slate-400">
                        {formatThreadTime(thread.updated_at)}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500">
                      {thread.last_message || "Start a fresh research thread"}
                    </p>
                    <p className="mt-2 text-[11px] uppercase tracking-[0.16em] text-slate-400">
                      {thread.message_count || 0} messages
                    </p>
                  </div>
                  {!thread.isDraft ? (
                    <span
                      className="material-symbols-outlined rounded p-1 text-[16px] text-slate-300 opacity-0 transition group-hover:opacity-100 hover:bg-slate-100 hover:text-red-500"
                      onClick={(event) => {
                        event.stopPropagation();
                        deleteThread(thread.thread_id);
                      }}
                    >
                      delete
                    </span>
                  ) : null}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-slate-200 p-4">
          <button
            className="w-full rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-100"
            onClick={clearHistory}
            type="button"
          >
            Clear all history
          </button>
        </div>
      </aside>

      <main className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-slate-200 bg-white px-6 py-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">auto_awesome</span>
                <h1 className="text-3xl font-semibold text-slate-900">Research Workspace</h1>
              </div>
              <p className="mt-2 text-sm text-slate-500">
                {activeThread?.title || "New chat"} ({messages.length} messages)
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {filters.map((filter) => (
                <button
                  key={filter.label}
                  className={`rounded-lg border px-4 py-2 text-sm ${
                    docType === filter.value
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-slate-200 bg-white text-slate-600"
                  }`}
                  onClick={() => setDocType(filter.value)}
                  type="button"
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
          <div className="mx-auto flex max-w-4xl flex-wrap gap-2">
            {scopes.map((scope) => (
              <button
                key={scope.label}
                className={`rounded-full border px-3 py-1 text-xs ${
                  issueDate === scope.value
                    ? "border-blue-600 bg-blue-600 text-white"
                    : "border-slate-200 bg-white text-slate-600"
                }`}
                onClick={() => setIssueDate(scope.value)}
                type="button"
              >
                {scope.label}
              </button>
            ))}
          </div>
        </div>

        <div
          ref={messageViewportRef}
          className="flex-1 overflow-y-auto px-6 py-8"
        >
          <div className="mx-auto max-w-4xl space-y-6">
            {historyLoading ? (
              <p className="text-sm text-slate-500">Loading chat history...</p>
            ) : messages.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
                <h2 className="text-xl font-semibold text-slate-900">Start a real research thread</h2>
                <p className="mt-3 text-sm text-slate-500">
                  New chats now stay in the sidebar so you can come back later and continue them, just like a threaded assistant workspace.
                </p>
              </div>
            ) : null}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" ? (
                  <div className="flex h-9 w-9 items-center justify-center rounded-full border border-blue-100 bg-blue-50">
                    <span className="material-symbols-outlined text-sm text-primary">smart_toy</span>
                  </div>
                ) : null}

                <div className={`max-w-[80%] ${message.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                  <div
                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                      message.role === "user"
                        ? "rounded-br-md bg-primary text-white"
                        : "rounded-bl-md border border-slate-200 bg-white text-slate-800"
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p>
                  </div>

                  {message.status === "sending" ? (
                    <span className="mt-2 text-xs text-slate-500">Sending...</span>
                  ) : null}
                  {message.status === "failed" ? (
                    <span className="mt-2 text-xs font-medium text-red-600">Failed to send. Please try again.</span>
                  ) : null}

                  {message.sources?.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.sources.map((source, idx) => (
                        source.url ? (
                          <a
                            key={`${idx}-${sourceText(source)}`}
                            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-primary hover:bg-blue-50"
                            href={source.url}
                            rel="noreferrer"
                            target="_blank"
                          >
                            {sourceText(source)}
                          </a>
                        ) : (
                          <span
                            key={`${idx}-${sourceText(source)}`}
                            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500"
                          >
                            {sourceText(source)}
                          </span>
                        )
                      ))}
                    </div>
                  ) : null}

                  <span className="mt-2 text-xs text-slate-400">{message.ts}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-slate-200 bg-white px-6 py-5">
          <div className="mx-auto max-w-4xl">
            {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
            <form onSubmit={sendMessage}>
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 shadow-sm">
                <span className="material-symbols-outlined text-slate-400">attach_file</span>
                <input
                  className="flex-1 bg-transparent text-sm text-slate-900 outline-none"
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder={issueDate ? `Ask about the ${issueDate} issue...` : "Ask about the AI archive..."}
                  type="text"
                  value={question}
                />
                <button
                  className="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={loading}
                >
                  <span className="material-symbols-outlined">
                    {loading ? "hourglass_top" : "send"}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
