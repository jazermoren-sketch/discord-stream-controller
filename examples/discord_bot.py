import os
import discord
from discord import app_commands
from discord.ext import commands

from discord_stream_controller import StreamController

TOKEN = os.environ["DISCORD_TOKEN"]
FFMPEG_OPTIONS = {"options": "-vn"}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
controller = StreamController()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="play", description="Add a direct audio/video URL to the queue")
@app_commands.describe(url="A direct stream URL supported by FFmpeg")
async def play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice is None:
        voice = await channel.connect()
    elif voice.channel != channel:
        await voice.move_to(channel)

    await controller.add(interaction.guild_id, url, added_by=interaction.user.id)
    if not voice.is_playing() and not voice.is_paused():
        source = await controller.start(interaction.guild_id)
        if source:
            voice.play(discord.FFmpegPCMAudio(source.url, **FFMPEG_OPTIONS))
    await interaction.response.send_message("Added to the queue and started when available.")


@bot.tree.command(name="skip", description="Skip the current stream")
async def skip(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
    source = await controller.skip(interaction.guild_id)
    if voice and source:
        voice.play(discord.FFmpegPCMAudio(source.url, **FFMPEG_OPTIONS))
    await interaction.response.send_message("Skipped.")


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
