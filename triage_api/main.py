from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .alerts import EmergencyAlertService
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    EmergencyContactsResponse,
    EmergencyContactsUpsertRequest,
    QueueActionRequest,
    SummaryRequest,
    SummaryResponse,
)
from .service import TriageService
from .store import TriageStore

def create_app() -> FastAPI:
    app = FastAPI(title="Mental Health Triage API", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.service = TriageService()
    app.state.store = TriageStore()
    app.state.alert_service = EmergencyAlertService(app.state.store)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/triage/analyze", response_model=AnalyzeResponse)
    def analyze(request: AnalyzeRequest, http_request: Request) -> AnalyzeResponse:
        service: TriageService = http_request.app.state.service
        store: TriageStore = http_request.app.state.store
        alert_service: EmergencyAlertService = http_request.app.state.alert_service
        user_id = request.user_id or request.session_id
        result = service.analyze(
            session_id=request.session_id,
            recent_messages=[message.model_dump() for message in request.recent_messages],
            prior_summary=request.prior_summary,
        )
        latest_user_message = next(
            (message.content for message in reversed(request.recent_messages) if message.role == "user"),
            request.recent_messages[-1].content,
        )
        store.record_analysis(request.session_id, user_id, latest_user_message, result)
        result["user_id"] = user_id
        result["emergency_alert"] = alert_service.trigger_if_needed(
            user_id=user_id,
            session_id=request.session_id,
            last_message=latest_user_message,
            result=result,
        )
        return AnalyzeResponse(**result)

    @app.post("/triage/summarize-history", response_model=SummaryResponse)
    def summarize_history(request: SummaryRequest, http_request: Request) -> SummaryResponse:
        service: TriageService = http_request.app.state.service
        summary = service.summarize_history([session.model_dump() for session in request.sessions])
        return SummaryResponse(prior_summary=summary)

    @app.post("/api/emergency-contacts", response_model=EmergencyContactsResponse)
    def upsert_emergency_contacts(
        request: EmergencyContactsUpsertRequest, http_request: Request
    ) -> EmergencyContactsResponse:
        store: TriageStore = http_request.app.state.store
        contacts = store.replace_contacts(
            request.user_id,
            [contact.model_dump() for contact in request.contacts],
        )
        return EmergencyContactsResponse(user_id=request.user_id, contacts=contacts)

    @app.get("/api/emergency-contacts/{user_id}", response_model=EmergencyContactsResponse)
    def get_emergency_contacts(user_id: str, http_request: Request) -> EmergencyContactsResponse:
        store: TriageStore = http_request.app.state.store
        return EmergencyContactsResponse(user_id=user_id, contacts=store.get_contacts(user_id))

    @app.get("/api/queue")
    def get_queue(http_request: Request) -> dict[str, list[dict]]:
        store: TriageStore = http_request.app.state.store
        return {"queue": store.get_queue()}

    @app.post("/api/queue/{session_id}/actions")
    def act_on_queue_item(
        session_id: str,
        request: QueueActionRequest,
        http_request: Request,
    ) -> dict:
        store: TriageStore = http_request.app.state.store
        if store.get_queue_item(session_id) is None:
            raise HTTPException(status_code=404, detail="Queue item not found.")

        action_messages = {
            "prioritize": request.note or "Counselor marked this session for immediate review.",
            "start_outreach": request.note or "Counselor started outreach for this session.",
            "resolve": request.note or "Counselor resolved this session.",
        }
        action_statuses = {
            "prioritize": "priority_review",
            "start_outreach": "outreach_started",
            "resolve": "resolved",
        }
        updated = store.update_status(
            session_id=session_id,
            status=action_statuses[request.action],
            message=action_messages[request.action],
        )
        return {
            "session_id": session_id,
            "action": request.action,
            "queue_item": updated,
        }

    @app.get("/api/audit")
    def get_audit(http_request: Request) -> dict[str, list[dict]]:
        store: TriageStore = http_request.app.state.store
        return {"audit": store.get_audit()}

    @app.get("/api/alerts")
    def get_alerts(http_request: Request) -> dict[str, list[dict]]:
        store: TriageStore = http_request.app.state.store
        return {"alerts": store.get_alerts()}

    return app


app = create_app()
