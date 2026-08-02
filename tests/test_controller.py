import pytest
from discord_stream_controller import StreamController, StreamStatus


@pytest.mark.asyncio
async def test_queue_lifecycle():
    c = StreamController()
    await c.add(1, "https://example.com/video.mp4")
    current = await c.start(1)
    assert current is not None
    assert current.url.endswith("video.mp4")
    assert (await c.snapshot(1)).status == StreamStatus.RUNNING


@pytest.mark.asyncio
async def test_rejects_invalid_url():
    c = StreamController()
    with pytest.raises(ValueError):
        await c.add(1, "video.mp4")


@pytest.mark.asyncio
async def test_pause_and_resume():
    c = StreamController()
    await c.add(1, "https://example.com/a.mp4")
    await c.start(1)
    assert await c.pause(1) is True
    assert (await c.snapshot(1)).status == StreamStatus.PAUSED
    assert await c.resume(1) is True
    assert (await c.snapshot(1)).status == StreamStatus.RUNNING


@pytest.mark.asyncio
async def test_pause_and_resume_fail_in_wrong_state():
    c = StreamController()
    assert await c.pause(1) is False
    assert await c.resume(1) is False


@pytest.mark.asyncio
async def test_skip_starts_next_source():
    c = StreamController()
    await c.add(1, "https://example.com/one.mp4")
    await c.add(1, "https://example.com/two.mp4")
    await c.start(1)
    current = await c.skip(1)
    assert current is not None
    assert current.url.endswith("two.mp4")
    assert await c.queue_size(1) == 0


@pytest.mark.asyncio
async def test_stop_can_keep_or_clear_queue():
    c = StreamController()
    await c.add(1, "https://example.com/one.mp4")
    await c.add(1, "https://example.com/two.mp4")
    await c.start(1)
    await c.stop(1)
    assert await c.queue_size(1) == 1
    await c.stop(1, clear_queue=True)
    assert await c.queue_size(1) == 0
    assert (await c.snapshot(1)).status == StreamStatus.IDLE


@pytest.mark.asyncio
async def test_remove_and_move_queue_items():
    c = StreamController()
    await c.add(1, "https://example.com/a.mp4")
    await c.add(1, "https://example.com/b.mp4")
    await c.add(1, "https://example.com/c.mp4")
    removed = await c.remove(1, 1)
    assert removed.url.endswith("b.mp4")
    await c.move(1, 1, 0)
    queue = await c.queue(1)
    assert [item.url[-5] for item in queue] == ["c", "a"]


@pytest.mark.asyncio
async def test_invalid_queue_indexes_raise():
    c = StreamController()
    with pytest.raises(IndexError):
        await c.remove(1, 0)
    await c.add(1, "https://example.com/a.mp4")
    with pytest.raises(IndexError):
        await c.move(1, 0, 1)


@pytest.mark.asyncio
async def test_guild_queues_are_isolated():
    c = StreamController()
    await c.add(1, "https://example.com/guild1.mp4")
    await c.add(2, "https://example.com/guild2.mp4")
    first = await c.start(1)
    second = await c.start(2)
    assert first is not None and "guild1" in first.url
    assert second is not None and "guild2" in second.url


@pytest.mark.asyncio
async def test_snapshot_is_independent_copy():
    c = StreamController()
    await c.add(1, "https://example.com/a.mp4")
    snapshot = await c.snapshot(1)
    snapshot.queue.clear()
    assert await c.queue_size(1) == 1
