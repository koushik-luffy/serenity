import { startTransition, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  CheckCheck,
  PhoneCall,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Siren,
  Sparkles,
  Users,
} from "lucide-react";

import {
  AlertEntry,
  AuditEntry,
  QueueEntry,
  classForSeverity,
  fetchJson,
  formatRelative,
  severityLabels,
  subtypeLabels,
} from "@/lib/triage";

type CounselorAction = "prioritize" | "start_outreach" | "resolve";

export default function CounselorDashboard() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isActing, setIsActing] = useState<CounselorAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedEntry = useMemo(
    () => queue.find((entry) => entry.session_id === selectedSessionId) ?? queue[0] ?? null,
    [queue, selectedSessionId],
  );

  const queueMetrics = useMemo(() => {
    const high = queue.filter((entry) => entry.severity === "high_crisis").length;
    const emergency = queue.filter((entry) => entry.emergency_flag).length;
    const avgRisk = queue.length
      ? Math.round(queue.reduce((sum, item) => sum + item.risk_score, 0) / queue.length)
      : 0;

    return { total: queue.length, high, emergency, avgRisk };
  }, [queue]);

  async function refreshOperationalData() {
    try {
      const [health, queueData, auditData, alertData] = await Promise.all([
        fetchJson<{ status: string }>("/health"),
        fetchJson<{ queue: QueueEntry[] }>("/api/queue"),
        fetchJson<{ audit: AuditEntry[] }>("/api/audit"),
        fetchJson<{ alerts: AlertEntry[] }>("/api/alerts"),
      ]);

      startTransition(() => {
        setBackendOnline(health.status === "ok");
        setQueue(queueData.queue);
        setAudit(auditData.audit);
        setAlerts(alertData.alerts);
        setSelectedSessionId((current) =>
          current && queueData.queue.some((entry) => entry.session_id === current)
            ? current
            : queueData.queue[0]?.session_id ?? null,
        );
      });
    } catch {
      setBackendOnline(false);
    }
  }

  useEffect(() => {
    refreshOperationalData();
    const interval = window.setInterval(refreshOperationalData, 5000);
    return () => window.clearInterval(interval);
  }, []);

  async function handleAction(action: CounselorAction) {
    if (!selectedEntry) return;
    setIsActing(action);
    setError(null);

    try {
      await fetchJson(`/api/queue/${selectedEntry.session_id}/actions`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      await refreshOperationalData();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to complete the counselor action.");
    } finally {
      setIsActing(null);
    }
  }

  return (
    <main className="min-h-screen bg-aurora px-4 py-4 text-ink md:px-6 lg:px-8">
      <div className="glass-panel soft-grid relative mx-auto max-w-[1600px] overflow-hidden rounded-[36px] border border-white/70 shadow-panel">
        <div className="absolute left-10 top-10 h-44 w-44 rounded-full bg-cyan-200/40 blur-3xl" />
        <div className="absolute right-20 top-8 h-44 w-44 rounded-full bg-pink-200/50 blur-3xl" />

        <div className="relative px-5 py-5 md:px-7 md:py-6 xl:px-8">
          <header className="flex flex-col gap-4 border-b border-line/70 pb-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-gradient-to-br from-white to-[#efe5ff] shadow-soft">
                <Brain className="h-7 w-7 text-[#7c70ff]" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Serenity counselor operations</p>
                <h1 className="mt-1 font-display text-3xl font-bold text-slate-900 md:text-4xl">
                  Priority queue and actions
                </h1>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm text-slate-500 shadow-soft">
                {backendOnline === false ? "Backend offline" : backendOnline === true ? "Live operations feed" : "Checking backend"}
              </div>
              <button
                onClick={refreshOperationalData}
                className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm text-slate-600 shadow-soft"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
              <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-white/70 bg-white/85 shadow-soft">
                <Bell className="h-5 w-5 text-slate-500" />
                {alerts.length > 0 && <span className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full bg-rose-400" />}
              </div>
            </div>
          </header>

          <section className="grid gap-6 pt-6 xl:grid-cols-[320px,minmax(0,1fr),360px]">
            <aside className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Priority list</p>
                  <h2 className="mt-2 font-display text-2xl font-bold text-slate-900">Active sessions</h2>
                </div>
                <Users className="h-5 w-5 text-[#7c70ff]" />
              </div>

              <div className="mt-5 space-y-3">
                {queue.length === 0 && (
                  <div className="rounded-[22px] bg-white/84 px-4 py-5 text-sm text-slate-500">
                    No live sessions yet. Use the user page to create one.
                  </div>
                )}

                {queue.map((entry, index) => (
                  <button
                    key={`${entry.session_id}-${entry.timestamp}`}
                    onClick={() => setSelectedSessionId(entry.session_id)}
                    className={`w-full rounded-[24px] border px-4 py-4 text-left transition ${
                      selectedEntry?.session_id === entry.session_id
                        ? "border-slate-900 bg-[#14182c] text-white shadow-soft"
                        : "border-white/80 bg-white/84 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.22em] opacity-60">#{index + 1} priority</p>
                        <p className="mt-1 text-sm font-semibold">{entry.user_id}</p>
                      </div>
                      <span
                        className={`rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${
                          selectedEntry?.session_id === entry.session_id
                            ? "border-white/20 bg-white/10 text-white"
                            : classForSeverity(entry.severity)
                        }`}
                      >
                        {severityLabels[entry.severity]}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 opacity-80">{entry.last_message}</p>
                    <div className="mt-3 flex items-center justify-between text-xs opacity-60">
                      <span>{subtypeLabels[entry.subtype]}</span>
                      <span>{formatRelative(entry.timestamp)}</span>
                    </div>
                  </button>
                ))}
              </div>
            </aside>

            <section className="glass-panel overflow-hidden rounded-[34px] border border-white/80 shadow-glow">
              <div className="flex flex-col gap-4 border-b border-line/60 px-5 py-5 md:flex-row md:items-end md:justify-between md:px-6">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Selected session</p>
                  <h2 className="mt-2 font-display text-4xl font-bold leading-tight text-slate-900">
                    {selectedEntry ? selectedEntry.user_id : "No session selected"}
                  </h2>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500">
                    Counselors can triage the live queue, mark priority cases, start outreach, and resolve sessions from here.
                  </p>
                </div>

                {selectedEntry && (
                  <div className={`rounded-full border px-4 py-2 text-sm font-semibold ${classForSeverity(selectedEntry.severity)}`}>
                    {severityLabels[selectedEntry.severity]} • {Math.round(selectedEntry.risk_score)}/100 risk
                  </div>
                )}
              </div>

              <div className="grid gap-6 px-5 py-5 md:px-6 xl:grid-cols-[minmax(0,1fr),280px]">
                <div className="space-y-4">
                  <div className="rounded-[30px] border border-white/80 bg-white/84 p-5 shadow-soft">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Latest message</p>
                    <p className="mt-4 text-[15px] leading-8 text-slate-700">
                      {selectedEntry ? selectedEntry.last_message : "No message available yet."}
                    </p>
                    <div className="mt-5 flex flex-wrap gap-2">
                      {(selectedEntry?.top_indicators.length ? selectedEntry.top_indicators : ["No indicators yet"]).map((indicator) => (
                        <span key={indicator} className="rounded-full border border-white/80 bg-slate-50 px-3 py-1 text-xs text-slate-500">
                          {indicator}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[30px] border border-white/80 bg-white/84 p-5 shadow-soft">
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Counselor actions</p>
                    <div className="mt-4 grid gap-3 md:grid-cols-3">
                      <button
                        onClick={() => void handleAction("prioritize")}
                        disabled={!selectedEntry || isActing !== null}
                        className="inline-flex items-center justify-center gap-2 rounded-[22px] bg-[#14182c] px-4 py-4 text-sm font-semibold text-white shadow-soft disabled:opacity-50"
                      >
                        {isActing === "prioritize" ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldAlert className="h-4 w-4" />}
                        Prioritize
                      </button>
                      <button
                        onClick={() => void handleAction("start_outreach")}
                        disabled={!selectedEntry || isActing !== null}
                        className="inline-flex items-center justify-center gap-2 rounded-[22px] border border-white/80 bg-white px-4 py-4 text-sm font-semibold text-slate-700 shadow-soft disabled:opacity-50"
                      >
                        {isActing === "start_outreach" ? <RefreshCw className="h-4 w-4 animate-spin" /> : <PhoneCall className="h-4 w-4" />}
                        Start outreach
                      </button>
                      <button
                        onClick={() => void handleAction("resolve")}
                        disabled={!selectedEntry || isActing !== null}
                        className="inline-flex items-center justify-center gap-2 rounded-[22px] border border-emerald-100 bg-emerald-50 px-4 py-4 text-sm font-semibold text-emerald-700 shadow-soft disabled:opacity-50"
                      >
                        {isActing === "resolve" ? <RefreshCw className="h-4 w-4 animate-spin" /> : <CheckCheck className="h-4 w-4" />}
                        Resolve
                      </button>
                    </div>
                    {error && (
                      <div className="mt-4 flex items-center gap-2 rounded-[18px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                        <AlertTriangle className="h-4 w-4" />
                        {error}
                      </div>
                    )}
                  </div>

                  <div className="rounded-[30px] border border-white/80 bg-white/84 p-5 shadow-soft">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Timeline</p>
                        <p className="text-sm font-semibold text-slate-800">Recent operational events</p>
                      </div>
                      <Sparkles className="h-5 w-5 text-[#7c70ff]" />
                    </div>
                    <div className="mt-4 space-y-3">
                      {audit
                        .filter((entry) => !selectedEntry || entry.session_id === selectedEntry.session_id || entry.user_id === selectedEntry.user_id)
                        .slice()
                        .reverse()
                        .slice(0, 5)
                        .map((entry) => (
                          <div key={`${entry.timestamp}-${entry.event}`} className="rounded-[20px] bg-slate-50 px-4 py-3">
                            <div className="flex items-center justify-between gap-3">
                              <span className="text-sm font-semibold text-slate-800">{entry.event.replace(/_/g, " ")}</span>
                              <span className="text-xs text-slate-400">{formatRelative(entry.timestamp)}</span>
                            </div>
                            <p className="mt-2 text-sm leading-6 text-slate-500">{entry.message}</p>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>

                <aside className="space-y-4">
                  {[
                    { label: "Queue", value: queueMetrics.total, icon: Users },
                    { label: "High crisis", value: queueMetrics.high, icon: Siren },
                    { label: "Emergency", value: queueMetrics.emergency, icon: ShieldAlert },
                    { label: "Avg risk", value: queueMetrics.avgRisk, icon: Activity },
                  ].map(({ label, value, icon: Icon }) => (
                    <div key={label} className="rounded-[26px] border border-white/80 bg-white/84 px-4 py-4 shadow-soft">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-50 text-[#7c70ff]">
                            <Icon className="h-5 w-5" />
                          </div>
                          <p className="text-sm text-slate-500">{label}</p>
                        </div>
                        <p className="font-display text-3xl font-bold text-slate-900">{value}</p>
                      </div>
                    </div>
                  ))}

                  <div className="rounded-[26px] border border-white/80 bg-white/84 p-4 shadow-soft">
                    <div className="flex items-center gap-3">
                      <ShieldCheck className="h-5 w-5 text-emerald-500" />
                      <div>
                        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Current status</p>
                        <p className="text-sm font-semibold text-slate-800">{selectedEntry?.status ?? "No active status"}</p>
                      </div>
                    </div>
                  </div>
                </aside>
              </div>
            </section>

            <aside className="space-y-4">
              <div className="glass-panel rounded-[30px] border border-white/80 p-5 shadow-soft">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Alerts</p>
                    <h3 className="mt-2 font-display text-2xl font-bold text-slate-900">Escalation feed</h3>
                  </div>
                  <Siren className="h-5 w-5 text-rose-500" />
                </div>

                <div className="mt-5 space-y-3">
                  {alerts.slice().reverse().slice(0, 6).map((alert) => (
                    <div key={alert.alert_id} className="rounded-[22px] border border-white/80 bg-white/84 px-4 py-4">
                      <div className="flex items-center justify-between gap-3">
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${classForSeverity(alert.severity)}`}>
                          {severityLabels[alert.severity]}
                        </span>
                        <span className="text-xs text-slate-400">{formatRelative(alert.timestamp)}</span>
                      </div>
                      <p className="mt-3 text-sm font-semibold text-slate-800">{alert.user_id}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-500">{alert.last_message}</p>
                      <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-400">{alert.status}</p>
                    </div>
                  ))}
                  {alerts.length === 0 && (
                    <div className="rounded-[22px] bg-white/84 px-4 py-5 text-sm text-slate-500">
                      No emergency alerts have been recorded yet.
                    </div>
                  )}
                </div>
              </div>
            </aside>
          </section>
        </div>
      </div>
    </main>
  );
}
