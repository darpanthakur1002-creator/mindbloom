from typing import Literal

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: dict[str, str] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    reply: str
    safety_note: str = "MindBloom is a wellbeing companion, not a substitute for medical care."


class HealthSummary(BaseModel):
    heart_rate: int = 72
    heart_rate_recorded_at: str | None = None
    sleep_hours: float = 7.7
    mood: Literal["positive", "steady", "low"] = "positive"
    brain_score: int = 82
    medication_adherence: int = 96


class HeartRateReadingCreate(BaseModel):
    heart_rate: int = Field(ge=30, le=220)
    source: str = Field(default="manual", min_length=1, max_length=40)


class HeartRateReading(BaseModel):
    heart_rate: int
    source: str
    recorded_at: str


class CheckInCreate(BaseModel):
    mood: Literal["positive", "steady", "low"]
    note: str = Field(default="", max_length=1000)


class CheckIn(BaseModel):
    id: int
    mood: Literal["positive", "steady", "low"]
    note: str
    created_at: str


class ActivityCompletionCreate(BaseModel):
    activity_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=160)
    kind: str = Field(default="activity", min_length=1, max_length=40)
    score: int = Field(default=0, ge=0, le=100000)


class ActivityProgress(BaseModel):
    activity_id: str
    title: str
    kind: str
    completions: int
    last_completed_at: str
    last_score: int = 0
    best_score: int = 0


class MemoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(default="", max_length=1000)


class Memory(BaseModel):
    id: int
    title: str
    detail: str
    created_at: str


class InviteCreate(BaseModel):
    contact: str = Field(min_length=3, max_length=200)


class Invite(BaseModel):
    id: int
    contact: str
    status: Literal["pending", "accepted"]
    created_at: str


class Dashboard(BaseModel):
    health_summary: HealthSummary
    latest_check_in: CheckIn | None = None
    activity_progress: list[ActivityProgress] = Field(default_factory=list)
    memories: list[Memory] = Field(default_factory=list)
