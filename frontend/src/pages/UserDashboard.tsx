import { startTransition, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bell,
  Brain,
  HeartHandshake,
  LoaderCircle,
  MessageSquareText,
  RefreshCw,
  SendHorizonal,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import {
  AnalyzeResponse,
  ChatMessage,
  ContactDraft,
  EmergencyContact,
  SessionRecord,
  USER_ID,
  SESSION_ID,
  buildAssistantReply,
  classForSeverity,
  fetchJson,
  formatTime,
  initialContactDraft,
  initialMessages,
  ringForSeverity,
  severityLabels,
  subtypeLabels,
} from "@/lib/triage";

export default function UserDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [priorSummary, setPriorSummary] = useState<string | null>(null);
  const [sessionHistory, setSessionHistory] = useState<SessionRecord[]>([]);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [contactDraft, setContactDraft] = useState<ContactDraft>(initialContactDraft);
  const [contactSaving, setContactSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signalCopy = useMemo(() => {
    if (!analysis) return "No live triage result yet";
    return `${severityLabels[analysis.severity]} severity • ${subtypeLabels[analysis.subtype]}`;
  }, [analysis]);

  async function refreshContactsAndHealth() {
    try {
      const [health, contactData] = await Promise.all([
        fetchJson<{ status: string }>("/health"),
        fetchJson<{ contacts: EmergencyContact[] }>(`/api/emergency-contacts/${USER_ID}`),
      ]);

      startTransition(() => {
        setBackendOnline(health.status === "ok");
        setContacts(contactData.contacts);
      });
    } catch {
      setBackendOnline(false);
    }
  }

  useEffect(() => {
    refreshContactsAndHealth();
  }, []);

  async function refreshPriorSummary(nextHistory: SessionRecord[]) {
    if (!nextHistory.length) {
      setPriorSummary(null);
      return;
    }

    const summary = await fetchJson<{ prior_summary: string }>("/triage/summarize-history", {
      method: "POST",
      body: JSON.stringify({ sessions: nextHistory }),
    });
    setPriorSummary(summary.prior_summary);
  }

  async function handleSendMessage() {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const analyze = await fetchJson<AnalyzeResponse>("/triage/analyze", {
        method: "POST",
        body: JSON.stringify({
          session_id: SESSION_ID,
          user_id: USER_ID,
          recent_messages: nextMessages.slice(-8).map((message) => ({
            role: message.role,
            content: message.content,
          })),
          prior_summary: priorSummary,
        }),
      });

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: buildAssistantReply(analyze),
        timestamp: new Date().toISOString(),
      };

      const nextHistory: SessionRecord[] = [
        ...sessionHistory.slice(-9),
        {
          session_id: `${SESSION_ID}-${sessionHistory.length + 1}`,
          final_severity: analyze.severity,
          subtype: analyze.subtype,
          emergency_flag: analyze.emergency_flag,
          days_ago: 0,
          notes: analyze.top_indicators.join(", ") || null,
        },
      ];

      setAnalysis(analyze);
      setMessages((current) => [...current, assistantMessage]);
      setSessionHistory(nextHistory);
      await refreshPriorSummary(nextHistory);
      await refreshContactsAndHealth();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to reach the triage backend.");
      setBackendOnline(false);
    } finally {
      setIsSending(false);
    }
  }

  async function handleSaveContact() {
    if (!contactDraft.name.trim() || !contactDraft.relationship.trim()) {
      setError("Add a name and relationship before saving.");
      return;
    }

    if (!contactDraft.phone_number.trim() && !contactDraft.email.trim()) {
      setError("Provide a phone number or email for the trusted contact.");
      return;
    }

    setContactSaving(true);
    setError(null);

    try {
      const response = await fetchJson<{ contacts: EmergencyContact[] }>("/api/emergency-contacts", {
        method: "POST",
        body: JSON.stringify({
          user_id: USER_ID,
          contacts: [
            {
              name: contactDraft.name.trim(),
              relationship: contactDraft.relationship.trim(),
              phone_number: contactDraft.phone_number.trim() || null,
              email: contactDraft.email.trim() || null,
              preferred_channel: contactDraft.preferred_channel,
              is_primary: true,
            },
          ],
        }),
      });

      setContacts(response.contacts);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save the trusted contact.");
    } finally {
      setContactSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-aurora px-4 py-4 text-ink md:px-6 lg:px-8">
      <div className="glass-panel soft-grid relative mx-auto max-w-[1550px] overflow-hidden rounded-[36px] border border-white/70 shadow-panel">
        <div className="absolute left-10 top-10 h-44 w-44 rounded-full bg-cyan-200/40 blur-3xl" />
        <div className="absolute right-16 top-12 h-44 w-44 rounded-full bg-pink-200/50 blur-3xl" />

        <div className="relative px-5 py-5 md:px-7 md:py-6 xl:px-8">
          <header className="flex flex-col gap-4 border-b border-line/70 pb-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-gradient-to-br from-white to-[#efe5ff] shadow-soft">
                <Brain className="h-7 w-7 text-[#7c70ff]" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Serenity user experience</p>
                <h1 className="mt-1 font-display text-3xl font-bold text-slate-900 md:text-4xl">
                  Calm support, live triage
                </h1>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm text-slate-500 shadow-soft">
                {backendOnline === false ? "Backend offline" : backendOnline === true ? "Protected by live backend" : "Checking backend"}
              </div>
              <button
                onClick={refreshContactsAndHealth}
                className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm text-slate-600 shadow-soft"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
              <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-white/70 bg-white/85 shadow-soft">
                <Bell className="h-5 w-5 text-slate-500" />
                {analysis?.emergency_alert.triggered && <span className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full bg-rose-400" />}
              </div>
            </div>
          </header>

          <section className="grid gap-6 pt-6 xl:grid-cols-[minmax(0,1.4fr),360px]">
            <div className="glass-panel overflow-hidden rounded-[34px] border border-white/80 shadow-glow">
              <div className="flex flex-col gap-4 border-b border-line/60 px-5 py-5 md:flex-row md:items-end md:justify-between md:px-6">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Main experience</p>
                  <h2 className="mt-2 font-display text-4xl font-bold leading-tight text-slate-900">
                    Chat stays first, simple, and reassuring.
                  </h2>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500">
                    This is the user-facing page. The chat is the hero, and the supporting cards stay lightweight:
                    current triage status, trusted contact settings, and calm context.
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <span className="rounded-full border border-white/80 bg-white/78 px-4 py-2 text-sm text-slate-600 shadow-soft">
                    Session {SESSION_ID}
                  </span>
                </div>
              </div>

              <div className="flex min-h-[720px] flex-col">
                <div className="flex items-center justify-between px-5 pb-4 pt-5 md:px-6">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${ringForSeverity(analysis?.severity ?? "low")} shadow-soft`}>
                      <MessageSquareText className="h-5 w-5 text-slate-800" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">Serenity conversation</p>
                      <p className="text-xs text-slate-400">{signalCopy}</p>
                    </div>
                  </div>

                  {analysis && (
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${classForSeverity(analysis.severity)}`}>
                      {severityLabels[analysis.severity]}
                    </span>
                  )}
                </div>

                <div className="scroll-hidden flex-1 overflow-y-auto px-5 pb-5 md:px-6">
                  <div className="space-y-5">
                    {messages.map((message) => (
                      <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-[78%] ${message.role === "user" ? "items-end" : "items-start"} flex flex-col gap-2`}>
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                            {message.role === "user" ? "You" : "Serenity"}
                          </div>
                          <div
                            className={`rounded-[28px] px-5 py-4 text-[15px] leading-7 shadow-soft ${
                              message.role === "user"
                                ? "rounded-br-[10px] bg-[#14182c] text-white"
                                : "rounded-bl-[10px] border border-white/80 bg-white/84 text-slate-700"
                            }`}
                          >
                            {message.content}
                          </div>
                          <div className="text-xs text-slate-400">{formatTime(message.timestamp)}</div>
                        </div>
                      </div>
                    ))}

                    {isSending && (
                      <div className="flex justify-start">
                        <div className="flex max-w-[78%] flex-col gap-2">
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Serenity</div>
                          <div className="flex items-center gap-2 rounded-[28px] rounded-bl-[10px] border border-white/80 bg-white/84 px-5 py-4 text-slate-500 shadow-soft">
                            <LoaderCircle className="h-4 w-4 animate-spin" />
                            Analyzing and updating support signals
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-t border-line/60 px-5 py-5 md:px-6">
                  <div className="rounded-[30px] border border-white/80 bg-white/84 p-3 shadow-soft">
                    <textarea
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          void handleSendMessage();
                        }
                      }}
                      rows={3}
                      placeholder="Share what is happening right now..."
                      className="w-full resize-none border-0 bg-transparent px-3 py-3 text-[15px] leading-7 text-slate-700 outline-none placeholder:text-slate-400"
                    />
                    <div className="flex flex-col gap-3 border-t border-line/50 px-3 pb-2 pt-3 md:flex-row md:items-center md:justify-between">
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">Live triage</span>
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">History-aware</span>
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">Safety routing</span>
                      </div>
                      <button
                        onClick={() => void handleSendMessage()}
                        disabled={isSending || !input.trim()}
                        className="inline-flex items-center justify-center gap-2 rounded-full bg-[#14182c] px-5 py-3 text-sm font-semibold text-white shadow-soft transition disabled:cursor-not-allowed disabled:opacity-45"
                      >
                        <SendHorizonal className="h-4 w-4" />
                        Send
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div className="mt-4 flex items-center gap-2 rounded-[22px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                      <AlertTriangle className="h-4 w-4" />
                      {error}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <aside className="space-y-4">
              <div className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-[#7c70ff]" />
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Current status</p>
                    <p className="text-sm font-semibold text-slate-800">{signalCopy}</p>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-[22px] bg-slate-50 px-4 py-3">
                    <p className="text-xs text-slate-400">Risk score</p>
                    <p className="mt-1 font-display text-3xl font-bold text-slate-900">
                      {analysis ? Math.round(analysis.risk_score) : "--"}
                    </p>
                  </div>
                  <div className="rounded-[22px] bg-slate-50 px-4 py-3">
                    <p className="text-xs text-slate-400">Confidence</p>
                    <p className="mt-1 font-display text-3xl font-bold text-slate-900">
                      {analysis ? `${Math.round(analysis.confidence * 100)}%` : "--"}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {(analysis?.top_indicators.length ? analysis.top_indicators : ["No indicators yet"]).map((indicator) => (
                    <span key={indicator} className="rounded-full border border-white/80 bg-white px-3 py-1 text-xs text-slate-500">
                      {indicator}
                    </span>
                  ))}
                </div>
              </div>

              <div className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="h-5 w-5 text-rose-500" />
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Emergency routing</p>
                    <p className="text-sm font-semibold text-slate-800">
                      {analysis?.emergency_alert.triggered ? `Triggered • ${analysis.emergency_alert.status}` : "Not triggered"}
                    </p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-500">
                  If the conversation crosses a crisis threshold, the counselor workspace and emergency-contact flow update automatically.
                </p>
              </div>

              <div className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
                <div className="flex items-center gap-3">
                  <HeartHandshake className="h-5 w-5 text-[#7c70ff]" />
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Trusted contact</p>
                    <p className="text-sm font-semibold text-slate-800">Personal emergency contact</p>
                  </div>
                </div>

                <div className="mt-4 grid gap-3">
                  <input
                    value={contactDraft.name}
                    onChange={(event) => setContactDraft((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Contact name"
                    className="rounded-[18px] border border-line bg-slate-50 px-4 py-3 text-sm outline-none"
                  />
                  <input
                    value={contactDraft.relationship}
                    onChange={(event) => setContactDraft((current) => ({ ...current, relationship: event.target.value }))}
                    placeholder="Relationship"
                    className="rounded-[18px] border border-line bg-slate-50 px-4 py-3 text-sm outline-none"
                  />
                  <input
                    value={contactDraft.phone_number}
                    onChange={(event) => setContactDraft((current) => ({ ...current, phone_number: event.target.value }))}
                    placeholder="Phone number"
                    className="rounded-[18px] border border-line bg-slate-50 px-4 py-3 text-sm outline-none"
                  />
                  <input
                    value={contactDraft.email}
                    onChange={(event) => setContactDraft((current) => ({ ...current, email: event.target.value }))}
                    placeholder="Email"
                    className="rounded-[18px] border border-line bg-slate-50 px-4 py-3 text-sm outline-none"
                  />
                  <button
                    onClick={() => void handleSaveContact()}
                    disabled={contactSaving}
                    className="inline-flex items-center justify-center gap-2 rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-soft disabled:opacity-50"
                  >
                    {contactSaving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <HeartHandshake className="h-4 w-4" />}
                    Save trusted contact
                  </button>
                </div>

                <div className="mt-4 space-y-2">
                  {contacts.map((contact) => (
                    <div key={contact.contact_id} className="rounded-[18px] bg-slate-50 px-4 py-3">
                      <p className="text-sm font-semibold text-slate-800">{contact.name}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {contact.relationship} • {contact.preferred_channel.toUpperCase()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {priorSummary && (
                <div className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Prior-session summary</p>
                  <p className="mt-3 text-sm leading-7 text-slate-600">{priorSummary}</p>
                </div>
              )}
            </aside>
          </section>
        </div>
      </div>
    </main>
  );
}
