from __future__ import annotations

import base64
import io
import json
import os
import ssl
import wave
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener

try:
    import truststore
except ImportError:  # pragma: no cover
    truststore = None


DEFAULT_CHAT_MODEL = "gemini-2.5-flash"
DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_TTS_VOICE = "Kore"
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


@dataclass
class ConversationResult:
    reply: str
    model: str
    audio_wav_base64: str | None = None
    fallback_used: bool = False
    notice: str | None = None


class ConversationServiceError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def build_fallback_conversation_result(
    *,
    recent_messages: list[dict[str, str]],
    triage_context: dict[str, Any] | None = None,
    provider_message: str | None = None,
) -> ConversationResult:
    latest_user_message = next(
        (message["content"].strip() for message in reversed(recent_messages) if message["role"] == "user" and message["content"].strip()),
        "what's been happening",
    )
    severity = str((triage_context or {}).get("severity") or "low")
    subtype = str((triage_context or {}).get("subtype") or "general_distress")

    fallback_templates = {
        "suicidal_ideation": (
            "What you just shared sounds serious, and I want to stay focused on safety with you. "
            "If you're alone or close to anything you could use to hurt yourself, please move toward another person or emergency help right now. "
            "Can you tell me whether you're alone at this moment?"
        ),
        "self_harm": (
            "I'm really glad you said that out loud. "
            "Because this sounds like a self-harm risk moment, please put distance between yourself and anything sharp or dangerous right now. "
            "Is there someone nearby who can stay with you?"
        ),
        "substance_overdose": (
            "This sounds like it needs urgent medical help, not just conversation. "
            "Please call emergency services now or get someone nearby to call for you immediately. "
            "Are you with another person right now?"
        ),
        "accident_injury": (
            "This sounds like an emergency situation. "
            "Please contact emergency services right away, or ask someone nearby to do it if you can't. "
            "Is help already on the way?"
        ),
        "abuse_violence": (
            "What you're describing feels unsafe, and I want to keep the next step very practical. "
            "Please create distance from the person or situation if you can do that safely, and contact emergency help or a trusted person right now. "
            "Are you physically away from them at this moment?"
        ),
        "panic_anxiety": (
            f"I'm here with you. From what you shared about \"{latest_user_message}\", this sounds like your system is really overloaded right now. "
            "Try one slow exhale longer than your inhale, and let me stay with one small moment of this. "
            "What feels strongest right now: your chest, your breathing, or your thoughts?"
        ),
        "depression_hopelessness": (
            f"What you shared about \"{latest_user_message}\" carries a lot of heaviness. "
            "I don't want to rush past that. Let's keep this very small and real for a moment. "
            "What has felt hardest to carry today: emptiness, exhaustion, or feeling disconnected?"
        ),
        "general_distress": (
            f"I can hear that something in \"{latest_user_message}\" is weighing on you, even if it feels hard to pin down neatly. "
            "We can stay with the real version of it instead of forcing it to sound tidy. "
            "What part of today has been the hardest on you emotionally?"
        ),
    }

    if severity == "high_crisis" and subtype not in fallback_templates:
        subtype = "general_distress"

    reply = fallback_templates.get(subtype, fallback_templates["general_distress"])
    provider_note = f" Provider message: {provider_message}" if provider_message else ""
    return ConversationResult(
        reply=reply,
        model="backup-support",
        audio_wav_base64=None,
        fallback_used=True,
        notice=(
            "Gemini is temporarily unavailable, so Serenity switched to backup support mode. "
            "Live safety triage is still active." + provider_note
        ),
    )


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""


def _extract_gemini_audio(payload: dict[str, Any]) -> bytes:
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData") or part.get("inline_data")
            if inline_data and isinstance(inline_data.get("data"), str):
                return base64.b64decode(inline_data["data"])
    return b""


def _pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()


class ConversationService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.chat_model = os.getenv("GEMINI_CHAT_MODEL", DEFAULT_CHAT_MODEL)
        self.tts_model = os.getenv("GEMINI_TTS_MODEL", DEFAULT_TTS_MODEL)
        self.tts_voice = os.getenv("GEMINI_TTS_VOICE", DEFAULT_TTS_VOICE)
        self._ssl_context = (
            truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            if truststore is not None
            else ssl.create_default_context()
        )
        self._opener = build_opener(
            ProxyHandler({}),
            HTTPSHandler(context=self._ssl_context),
        )

    def respond(
        self,
        *,
        recent_messages: list[dict[str, str]],
        triage_context: dict[str, Any] | None = None,
        prior_summary: str | None = None,
        include_audio: bool = False,
    ) -> ConversationResult:
        if not self.api_key:
            raise ConversationServiceError(503, "GEMINI_API_KEY is not configured.")

        reply = self._respond_with_gemini(
            recent_messages=recent_messages,
            triage_context=triage_context,
            prior_summary=prior_summary,
        )
        audio_wav_base64: str | None = None
        if include_audio:
            audio_wav_base64 = self._speak_with_gemini(reply)
        return ConversationResult(reply=reply, model=self.chat_model, audio_wav_base64=audio_wav_base64)

    def _respond_with_gemini(
        self,
        *,
        recent_messages: list[dict[str, str]],
        triage_context: dict[str, Any] | None,
        prior_summary: str | None,
    ) -> str:
        triage_summary = (
            json.dumps(triage_context, ensure_ascii=True)
            if triage_context is not None
            else "No triage context was supplied."
        )
        history_summary = prior_summary or "No prior summary available."
        contents: list[dict[str, Any]] = []
        for message in recent_messages:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message["content"]}]})

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are Serenity, a warm, emotionally attuned, trauma-informed mental health support companion. "
                            "Sound like a calm, thoughtful counselor in a live conversation, not a customer support bot. "
                            "Use natural language, emotional precision, gentle reflection, and grounded follow-up questions. "
                            "Do not diagnose, do not claim to be licensed, and do not sound robotic or generic. "
                            "Avoid canned lines like 'that sounds hard' unless you immediately anchor them to a concrete detail from the user's words. "
                            "Reference one specific feeling, event, relationship, or body sensation from the latest user message so the reply feels personal. "
                            "Keep replies under 140 words unless there is immediate danger. "
                            "Usually reflect the user's emotion in one sentence, offer one grounded observation or coping step, and ask one focused follow-up question. "
                            "Do not write lists, disclaimers, or policy-style language unless safety is urgent. "
                            "If the triage context suggests high crisis, self-harm, overdose, abuse, or immediate danger, "
                            "shift into a calm crisis-support tone, speak more directly, and encourage urgent human help, emergency services, or immediate distance from the person or means involved. "
                            f"Triage context: {triage_summary}. Prior summary: {history_summary}."
                        )
                    }
                ]
            },
            "contents": contents,
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 260},
        }
        parsed = self._call_gemini(self.chat_model, payload)
        reply = _extract_gemini_text(parsed)
        if not reply:
            raise ValueError("No output text returned from Gemini response.")
        return reply

    def _speak_with_gemini(self, text: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": f"Say warmly and calmly: {text}"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": self.tts_voice}
                    }
                },
            },
            "model": self.tts_model,
        }
        parsed = self._call_gemini(self.tts_model, payload)
        pcm_audio = _extract_gemini_audio(parsed)
        if not pcm_audio:
            raise ValueError("No audio returned from Gemini TTS response.")
        wav_bytes = _pcm_to_wav_bytes(pcm_audio)
        return base64.b64encode(wav_bytes).decode("ascii")

    def _call_gemini(self, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            GEMINI_API_URL_TEMPLATE.format(model=model),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=40) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            message = f"Gemini request failed with HTTP {exc.code}."
            try:
                parsed = json.loads(detail)
                message = parsed.get("error", {}).get("message", message)
            except json.JSONDecodeError:
                pass
            raise ConversationServiceError(exc.code, message) from exc
        except (URLError, TimeoutError) as exc:
            raise ConversationServiceError(503, "Gemini network request failed.") from exc
        return json.loads(body)
