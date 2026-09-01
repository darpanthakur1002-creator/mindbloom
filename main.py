import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import (
    ActivityCompletionCreate,
    ActivityProgress,
    AssistantRequest,
    AssistantResponse,
    CheckIn,
    CheckInCreate,
    Dashboard,
    HeartRateReading,
    HeartRateReadingCreate,
    HealthSummary,
    Invite,
    InviteCreate,
    Memory,
    MemoryCreate,
)
from .storage import (
    activity_progress,
    complete_activity,
    create_check_in,
    create_invite,
    create_memory,
    latest_check_in,
    latest_heart_rate,
    list_memories,
    create_heart_rate,
)

app = FastAPI(title=settings.app_name, version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_user(x_user_id: str | None = Header(default=None)) -> str:
    return x_user_id or "logged-in-user"


def health_summary_for(user_id: str) -> HealthSummary:
    check_in = latest_check_in(user_id)
    heart_rate = latest_heart_rate(user_id)
    return HealthSummary(
        mood=check_in["mood"] if check_in else "positive",
        heart_rate=heart_rate["heart_rate"] if heart_rate else 72,
        heart_rate_recorded_at=heart_rate["recorded_at"] if heart_rate else None,
    )


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/api/health/summary", response_model=HealthSummary, tags=["health"])
def health_summary(x_user_id: str | None = Header(default=None)) -> HealthSummary:
    return health_summary_for(current_user(x_user_id))


@app.post("/api/health/heart-rate", response_model=HeartRateReading, tags=["health"])
def save_heart_rate(request: HeartRateReadingCreate, x_user_id: str | None = Header(default=None)) -> HeartRateReading:
    return HeartRateReading(**create_heart_rate(current_user(x_user_id), request.heart_rate, request.source))


@app.get("/api/dashboard", response_model=Dashboard, tags=["dashboard"])
def dashboard(x_user_id: str | None = Header(default=None)) -> Dashboard:
    user = current_user(x_user_id)
    check_in = latest_check_in(user)
    return Dashboard(
        health_summary=health_summary_for(user),
        latest_check_in=check_in,
        activity_progress=activity_progress(user),
        memories=list_memories(user),
    )


@app.post("/api/check-ins", response_model=CheckIn, tags=["wellbeing"])
def save_check_in(request: CheckInCreate, x_user_id: str | None = Header(default=None)) -> CheckIn:
    return CheckIn(**create_check_in(current_user(x_user_id), request.mood, request.note))


@app.post("/api/activity-completions", response_model=ActivityProgress, tags=["activities"])
def save_activity(request: ActivityCompletionCreate, x_user_id: str | None = Header(default=None)) -> ActivityProgress:
    return ActivityProgress(**complete_activity(current_user(x_user_id), request.activity_id, request.title, request.kind, request.score))


@app.get("/api/activity-progress", response_model=list[ActivityProgress], tags=["activities"])
def get_activity_progress(x_user_id: str | None = Header(default=None)) -> list[ActivityProgress]:
    return [ActivityProgress(**item) for item in activity_progress(current_user(x_user_id))]


@app.get("/api/memories", response_model=list[Memory], tags=["memories"])
def get_memories(x_user_id: str | None = Header(default=None)) -> list[Memory]:
    return [Memory(**item) for item in list_memories(current_user(x_user_id))]


@app.post("/api/memories", response_model=Memory, tags=["memories"])
def save_memory(request: MemoryCreate, x_user_id: str | None = Header(default=None)) -> Memory:
    return Memory(**create_memory(current_user(x_user_id), request.title, request.detail))


@app.post("/api/invites", response_model=Invite, tags=["family"])
def save_invite(request: InviteCreate, x_user_id: str | None = Header(default=None)) -> Invite:
    return Invite(**create_invite(current_user(x_user_id), request.contact))


def _fallback_assistant_reply(question: str) -> str:
    if any(word in question for word in ("memory", "remember", "recall")):
        return "Try one small memory exercise: name the place, person, and feeling connected to the moment. You can also save the detail in Memory Capsule."
    if any(word in question for word in ("worried", "worry", "stress", "anxious", "doubt")):
        return "Take one slow breath, name what is worrying you, and choose the smallest helpful next step. If the worry feels overwhelming or urgent, speak with a qualified professional."
    if any(word in question for word in ("game", "activity", "exercise")):
        return "A gentle place to start is a short memory game or a daily check-in. Choose the activity that feels comfortable today; there is no need to rush."
    if any(word in question for word in ("heart", "bpm", "sleep", "health")):
        return "I can help you notice wellbeing patterns, but I cannot diagnose or interpret medical symptoms. Review your readings over time and contact a healthcare professional for concerns."
    return "I’m here with you. Tell me a little more about your question, and I’ll help you think through a calm, practical next step."


def _openai_assistant_reply(message: str) -> str | None:
    api_key = settings.ai_api_key.strip()
    if settings.ai_provider.lower() != "openai" or not api_key or api_key == "replace-me":
        return None

    payload = json.dumps({
        "model": settings.ai_model,
        "temperature": 0.4,
        "max_tokens": 350,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are MindBloom AI, a warm and concise wellbeing companion for older adults and caregivers. "
                    "Answer the user's question clearly in plain language. Do not diagnose, prescribe, or replace a doctor. "
                    "For urgent medical or safety concerns, advise contacting local emergency services or a qualified professional."
                ),
            },
            {"role": "user", "content": message},
        ],
    }).encode("utf-8")
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply.strip() or None
    except (OSError, URLError, ValueError, KeyError, IndexError):
        return None


@app.post("/api/assistant", response_model=AssistantResponse, tags=["assistant"])
def assistant(request: AssistantRequest) -> AssistantResponse:
    message = request.message.strip()
    reply = _openai_assistant_reply(message) or _fallback_assistant_reply(message.lower())
    return AssistantResponse(
        reply=reply
    )
