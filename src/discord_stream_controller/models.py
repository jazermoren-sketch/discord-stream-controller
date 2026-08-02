from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class StreamStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class MediaSource:
    url: str
    title: str | None = None
    added_by: int | None = None


@dataclass(slots=True)
class StreamSession:
    queue: list[MediaSource]
    current: MediaSource | None = None
    status: StreamStatus = StreamStatus.IDLE
    started_at: datetime | None = None
