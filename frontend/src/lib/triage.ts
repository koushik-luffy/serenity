export type ChatRole = "user" | "assistant";
export type Severity = "low" | "medium" | "high_crisis";
export type Subtype =
  | "suicidal_ideation"
  | "self_harm"
  | "panic_anxiety"
  | "depression_hopelessness"
  | "abuse_violence"
  | "substance_overdose"
  | "accident_injury"
  | "general_distress";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
};

export type SessionRecord = {
  session_id: string;
  final_severity: Severity;
  subtype: Subtype;
  emergency_flag: boolean;
  days_ago: number;
  notes: string | null;
};

export type AnalyzeResponse = {
  session_id: string;
  user_id: string;
  severity: Severity;
  subtype: Subtype;
  emergency_flag: boolean;
  risk_score: number;
  confidence: number;
  top_indicators: string[];
  safe_fail_escalated: boolean;
  emergency_alert: {
    triggered: boolean;
    status: "not_triggered" | "no_contacts" | "simulated";
    deliveries: Array<{
      contact_name: string;
      channel: "sms" | "email";
      target: string;
      status: "simulated" | "skipped";
      reason?: string | null;
    }>;
  };
};

export type QueueEntry = {
  session_id: string;
  user_id: string;
  severity: Severity;
  subtype: Subtype;
  emergency_flag: boolean;
  risk_score: number;
  confidence: number;
  last_message: string;
  top_indicators: string[];
  status: string;
  timestamp: string;
};

export type AuditEntry = {
  session_id?: string;
  user_id: string;
  severity: Severity;
  subtype: Subtype;
  message: string;
  timestamp: string;
  event: string;
  emergency_flag: boolean;
  risk_score: number;
};

export type AlertEntry = {
  alert_id: string;
  user_id: string;
  session_id: string;
  severity: Severity;
  risk_score: number;
  status: string;
  last_message: string;
  timestamp: string;
};

export type EmergencyContact = {
  contact_id: string;
  name: string;
  relationship: string;
  phone_number?: string | null;
  email?: string | null;
  preferred_channel: "sms" | "email";
  is_primary: boolean;
  created_at: string;
};

export type ContactDraft = {
  name: string;
  relationship: string;
  phone_number: string;
  email: string;
  preferred_channel: "sms" | "email";
};

export const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8000";
export const SESSION_ID = "anna-session-live";
export const USER_ID = "anna-counselor-demo";

export const subtypeLabels: Record<Subtype, string> = {
  suicidal_ideation: "Suicidal ideation",
  self_harm: "Self-harm",
  panic_anxiety: "Panic and anxiety",
  depression_hopelessness: "Hopelessness",
  abuse_violence: "Abuse or violence",
  substance_overdose: "Substance overdose",
  accident_injury: "Accident or injury",
  general_distress: "General distress",
};

export const severityLabels: Record<Severity, string> = {
  low: "Low",
  medium: "Medium",
  high_crisis: "High crisis",
};

export const initialContactDraft: ContactDraft = {
  name: "Aisha Khan",
  relationship: "Sister",
  phone_number: "+911234567890",
  email: "",
  preferred_channel: "sms",
};

export const initialMessages: ChatMessage[] = [
  {
    id: crypto.randomUUID(),
    role: "assistant",
    content:
      "I'm Serenity. Tell me what's happening right now, and I'll triage the conversation live while the counselor workspace updates in the background.",
    timestamp: new Date().toISOString(),
  },
];

export function classForSeverity(severity: Severity) {
  if (severity === "high_crisis") return "bg-rose-100 text-rose-600 border-rose-200";
  if (severity === "medium") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-emerald-100 text-emerald-700 border-emerald-200";
}

export function ringForSeverity(severity: Severity) {
  if (severity === "high_crisis") return "from-rose-300/60 via-pink-300/40 to-orange-200/40";
  if (severity === "medium") return "from-amber-200/60 via-orange-200/40 to-rose-200/30";
  return "from-cyan-200/60 via-emerald-200/40 to-sky-200/40";
}

export function buildAssistantReply(result: AnalyzeResponse) {
  const copy: Record<Subtype, string> = {
    suicidal_ideation:
      "Thank you for saying that clearly. I'm marking this conversation as high priority and keeping the safety pathway active. If there is immediate danger, contact emergency help or a trusted person right now.",
    self_harm:
      "I'm glad you told me. I'm treating this as an urgent safety conversation. If you can, move anything sharp or dangerous farther away while support is being routed.",
    panic_anxiety:
      "This reads like an elevated panic response. Stay with one slow breath at a time. I've marked the session for fast counselor review while we keep the conversation grounded.",
    depression_hopelessness:
      "This sounds deeply heavy. I'm holding the conversation at an elevated level so the counselor side sees it quickly. Tell me what feels hardest in this exact moment.",
    abuse_violence:
      "Your safety matters first. I'm escalating this for urgent review. If someone is actively hurting you or nearby, move to the safest place you can and contact emergency help immediately.",
    substance_overdose:
      "This sounds like a medical emergency. I'm activating the highest-priority path. Contact emergency services immediately or ask someone nearby to call now.",
    accident_injury:
      "This sounds like an emergency situation. I'm routing it at the highest level. Please contact emergency services right away if that has not happened yet.",
    general_distress:
      "I'm here with you. I've logged the current distress level and updated the counselor view. Keep going in your own words and I'll continue tracking urgency.",
  };

  return copy[result.subtype];
}

export function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatRelative(value: string) {
  const diff = Date.now() - new Date(value).getTime();
  const mins = Math.max(0, Math.round(diff / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}
