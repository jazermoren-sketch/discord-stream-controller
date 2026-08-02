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
