import pytest

from discord_stream_controller import VoiceStreamController


class FakeVoiceClient:
    def __init__(self, channel=None):
        self.channel = channel
        self.playing = False
        self.paused = False
        self.connected = True
        self.moved_to = None
        self.disconnected = False

    def is_connected(self):
        return self.connected

    def is_playing(self):
        return self.playing

    def is_paused(self):
        return self.paused

    async def move_to(self, channel):
        self.channel = channel
        self.moved_to = channel

    def pause(self):
        self.playing = False
        self.paused = True

    def resume(self):
        self.playing = True
        self.paused = False

    def stop(self):
        self.playing = False
        self.paused = False

    async def disconnect(self):
        self.connected = False
        self.disconnected = True


class FakeChannel:
    def __init__(self):
        self.client = FakeVoiceClient(self)
        self.connect_calls = 0

    async def connect(self):
        self.connect_calls += 1
        return self.client


class FakeGuild:
    def __init__(self, guild_id=123, voice_client=None):
        self.id = guild_id
        self.voice_client = voice_client


@pytest.mark.asyncio
async def test_connects_to_empty_channel():
    controller = VoiceStreamController()
    channel = FakeChannel()
    guild = FakeGuild()

    client = await controller.connect(guild, channel)

    assert client is channel.client
    assert channel.connect_calls == 1


@pytest.mark.asyncio
async def test_moves_existing_client():
    old_channel = FakeChannel()
    new_channel = FakeChannel()
    client = FakeVoiceClient(old_channel)
    guild = FakeGuild(123, client)

    controller = VoiceStreamController()
    result = await controller.connect(guild, new_channel)

    assert result is client
    assert client.channel is new_channel


@pytest.mark.asyncio
async def test_pause_and_resume():
    controller = VoiceStreamController()
    client = FakeVoiceClient()
    client.playing = True
    controller._clients[123] = client

    assert await controller.pause(123) is True
    assert client.paused is True

    assert await controller.resume(123) is True
    assert client.playing is True


@pytest.mark.asyncio
async def test_pause_without_playback():
    controller = VoiceStreamController()

    assert await controller.pause(999) is False


@pytest.mark.asyncio
async def test_stop():
    controller = VoiceStreamController()
    client = FakeVoiceClient()
    client.playing = True
    controller._clients[123] = client

    assert await controller.stop(123) is True
    assert client.playing is False


@pytest.mark.asyncio
async def test_disconnect():
    controller = VoiceStreamController()
    client = FakeVoiceClient()
    controller._clients[123] = client

    assert await controller.disconnect(123) is True
    assert client.disconnected is True
    assert 123 not in controller._clients


@pytest.mark.asyncio
async def test_invalid_url():
    controller = VoiceStreamController()
    guild = FakeGuild()
    channel = FakeChannel()

    with pytest.raises(ValueError, match="http"):
        await controller.play(guild, channel, "video.mp4")
