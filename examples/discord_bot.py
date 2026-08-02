import asyncio
import os

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

from discord_stream_controller import StreamController

TOKEN = os.environ["DISCORD_TOKEN"]
FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}
YTDLP_OPTIONS = {"format": "bestaudio/best", "noplaylist": True, "quiet": True, "no_warnings": True}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
controller = StreamController()


def extract_stream(url: str) -> tuple[str, str]:
    with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = next(entry for entry in info["entries"] if entry)
        return info["url"], info.get("title") or url


async def play_next(guild_id: int, voice: discord.VoiceClient):
    source = await controller.start(guild_id)
    if source is None:
        return
    try:
        stream_url, title = await asyncio.to_thread(extract_stream, source.url)
        audio = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)

        def after(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(play_next(guild_id, voice), bot.loop)

        voice.play(audio, after=after)
        print(f"Playing: {title}")
    except Exception as exc:
        print(f"Could not extract {source.url}: {exc}")
        await controller.skip(guild_id)
        await play_next(guild_id, voice)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="play", description="Play a YouTube or supported website URL")
@app_commands.describe(url="YouTube link or another URL supported by yt-dlp")
async def play(interaction: discord.Interaction, url: str):
    if interaction.guild is None:
        await interaction.response.send_message("This command only works in a server.", ephemeral=True)
        return
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client
    if voice is None:
        voice = await channel.connect()
    elif voice.channel != channel:
        await voice.move_to(channel)

    item = await controller.add(interaction.guild_id, url, added_by=interaction.user.id)
    await interaction.response.send_message(f"Added to queue: {item.url}")
    if not voice.is_playing() and not voice.is_paused():
        await play_next(interaction.guild_id, voice)


@bot.tree.command(name="skip", description="Skip the current stream")
async def skip(interaction: discord.Interaction):
    if interaction.guild is None:
        return
    voice = interaction.guild.voice_client
    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
        await interaction.response.send_message("Skipped.")
    else:
        await interaction.response.send_message("Nothing is playing.", ephemeral=True)


@bot.tree.command(name="pause", description="Pause playback")
async def pause(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice and voice.is_playing() and await controller.pause(interaction.guild_id):
        voice.pause()
        await interaction.response.send_message("Paused.")
    else:
        await interaction.response.send_message("Nothing is playing.", ephemeral=True)


@bot.tree.command(name="resume", description="Resume playback")
async def resume(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice and voice.is_paused() and await controller.resume(interaction.guild_id):
        voice.resume()
        await interaction.response.send_message("Resumed.")
    else:
        await interaction.response.send_message("Nothing is paused.", ephemeral=True)


@bot.tree.command(name="stop", description="Stop and clear the queue")
async def stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice:
        voice.stop()
        await voice.disconnect()
    await controller.clear(interaction.guild_id)
    await interaction.response.send_message("Stopped and cleared the queue.")


bot.run(TOKEN)
