from __future__ import annotations

from typing import Any


class VoiceStreamController:
    """Optional discord.py adapter for playing a URL's audio in a voice channel.

    The bot may connect to an empty voice channel. This adapter handles voice
    connection and FFmpeg audio playback; it does not implement Discord video
    screen sharing/Go Live.
    """

    def __init__(self, *, ffmpeg_executable: str = "ffmpeg", before_options: str = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5") -> None:
        self.ffmpeg_executable = ffmpeg_executable
        self.before_options = before_options
        self._clients: dict[int, Any] = {}

    @staticmethod
    def _discord() -> Any:
        try:
            import discord
        except ImportError as exc:
            raise RuntimeError("Discord support requires: pip install 'discord-stream-controller[discord]'") from exc
        return discord

    async def connect(self, guild: Any, channel: Any) -> Any:
        client = getattr(guild, "voice_client", None)
        if client and client.is_connected():
            if client.channel != channel:
                await client.move_to(channel)
        else:
            client = await channel.connect()
        self._clients[guild.id] = client
        return client

    async def play(self, guild: Any, channel: Any, url: str, *, volume: float = 1.0) -> None:
        if not url.startswith(("http://", "https://")):
            raise ValueError("Stream URL must start with http:// or https://")
        discord = self._discord()
        client = await self.connect(guild, channel)
        if client.is_playing() or client.is_paused():
            client.stop()
        source = discord.FFmpegPCMAudio(url, executable=self.ffmpeg_executable, before_options=self.before_options)
        client.play(discord.PCMVolumeTransformer(source, volume=volume))

    async def pause(self, guild_id: int) -> bool:
        client = self._clients.get(guild_id)
        if not client or not client.is_playing():
            return False
        client.pause()
        return True

    async def resume(self, guild_id: int) -> bool:
        client = self._clients.get(guild_id)
        if not client or not client.is_paused():
            return False
        client.resume()
        return True

    async def stop(self, guild_id: int, *, disconnect: bool = False) -> bool:
        client = self._clients.get(guild_id)
        if not client:
            return False
        if client.is_playing() or client.is_paused():
            client.stop()
        if disconnect and client.is_connected():
            await client.disconnect()
            self._clients.pop(guild_id, None)
        return True

    async def disconnect(self, guild_id: int) -> bool:
        client = self._clients.pop(guild_id, None)
        if not client or not client.is_connected():
            return False
        await client.disconnect()
        return True
