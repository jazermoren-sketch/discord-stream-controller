import asyncio
from datetime import datetime, timezone
from .models import MediaSource, StreamSession, StreamStatus


class StreamController:
    """Async, per-guild media queue and playback-state controller."""

    def __init__(self):
        self._sessions: dict[int, StreamSession] = {}
        self._locks: dict[int, asyncio.Lock] = {}

    def _session(self, guild_id: int) -> StreamSession:
        return self._sessions.setdefault(guild_id, StreamSession(queue=[]))

    def _lock(self, guild_id: int) -> asyncio.Lock:
        return self._locks.setdefault(guild_id, asyncio.Lock())

    async def add(self, guild_id: int, url: str, *, title: str | None = None,
                  added_by: int | None = None) -> MediaSource:
        if not url.startswith(("https://", "http://")):
            raise ValueError("Source URL must start with http:// or https://")
        source = MediaSource(url=url, title=title, added_by=added_by)
        async with self._lock(guild_id):
            self._session(guild_id).queue.append(source)
        return source

    async def start(self, guild_id: int) -> MediaSource | None:
        async with self._lock(guild_id):
            session = self._session(guild_id)
            if session.current is None and session.queue:
                session.current = session.queue.pop(0)
            if session.current:
                session.status = StreamStatus.RUNNING
                if session.started_at is None:
                    session.started_at = datetime.now(timezone.utc)
            return session.current

    async def skip(self, guild_id: int) -> MediaSource | None:
        async with self._lock(guild_id):
            session = self._session(guild_id)
            session.current = None
            session.status = StreamStatus.IDLE
            session.started_at = None
        return await self.start(guild_id)

    async def pause(self, guild_id: int) -> bool:
        async with self._lock(guild_id):
            session = self._session(guild_id)
            if session.status != StreamStatus.RUNNING:
                return False
            session.status = StreamStatus.PAUSED
            return True

    async def resume(self, guild_id: int) -> bool:
        async with self._lock(guild_id):
            session = self._session(guild_id)
            if session.status != StreamStatus.PAUSED:
                return False
            session.status = StreamStatus.RUNNING
            return True

    async def stop(self, guild_id: int, *, clear_queue: bool = False) -> None:
        async with self._lock(guild_id):
            session = self._session(guild_id)
            session.current = None
            session.status = StreamStatus.IDLE
            session.started_at = None
            if clear_queue:
                session.queue.clear()

    async def clear(self, guild_id: int) -> None:
        await self.stop(guild_id, clear_queue=True)

    async def remove(self, guild_id: int, index: int) -> MediaSource:
        async with self._lock(guild_id):
            queue = self._session(guild_id).queue
            try:
                return queue.pop(index)
            except IndexError as exc:
                raise IndexError("Queue index is out of range") from exc

    async def move(self, guild_id: int, from_index: int, to_index: int) -> None:
        async with self._lock(guild_id):
            queue = self._session(guild_id).queue
            if not 0 <= from_index < len(queue):
                raise IndexError("Source queue index is out of range")
            if not 0 <= to_index < len(queue):
                raise IndexError("Destination queue index is out of range")
            source = queue.pop(from_index)
            queue.insert(to_index, source)

    async def queue(self, guild_id: int) -> list[MediaSource]:
        async with self._lock(guild_id):
            return list(self._session(guild_id).queue)

    async def queue_size(self, guild_id: int) -> int:
        async with self._lock(guild_id):
            return len(self._session(guild_id).queue)

    async def snapshot(self, guild_id: int) -> StreamSession:
        async with self._lock(guild_id):
            s = self._session(guild_id)
            return StreamSession(list(s.queue), s.current, s.status, s.started_at)
