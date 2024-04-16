import asyncio
from io import BytesIO
import discord
from discord.ext import commands
from aiogtts import aiogTTS
import aiohttp
import os
from audiofix import FFmpegPCMAudio


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiogtts = aiogTTS()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # Ignore the bot itself and other bots
        if member == self.bot.user or member.bot:
            return

        # Ignore if the user is just muted or deafened
        if before.channel == after.channel:
            return

        # Leaving a voice channel or going afk
        if before.channel is not None:
            if after.channel == before.channel.guild.afk_channel:
                await self.afk_user(member, before.channel)
            else:
                await self.depart_user(member, before.channel)

        # Joining a voice channel
        if (
            after.channel is not None
            and after.channel != before.channel.guild.afk_channel
        ):
            await self.greet_user(member)

    async def greet_user(self, member: discord.Member):
        await self.say_line(f"{member.name} has joined.", member.voice.channel)

    async def depart_user(self, member: discord.Member, channel: discord.VoiceChannel):
        await self.say_line(f"{member.name} has left.", channel)

    async def afk_user(self, member: discord.Member, channel: discord.VoiceChannel):
        await self.say_line(f"{member.name} went afk", channel)

    async def say_line(self, line: str, channel: discord.VoiceChannel):
        buffer = BytesIO()

        tts_url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}".format(
            voice_id="EXAVITQu4vr4xnSDxMaL"
        )
        model_id = "eleven_turbo_v2"
        formatted_message = {
            "model_id": model_id,
            "text": line,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                tts_url,
                headers={
                    "Content-Type": "application/json",
                    "xi-api-key": os.environ["XI_API_KEY"],
                },
                json=formatted_message,
            ) as response:
                if response.status == 200:
                    buffer = BytesIO(await response.read())
                else:
                    print(
                        "ElevenLabs Request failed with status code:", response.status
                    )
                    print("Response content:", await response.text())
                    print("Falling back to aiogTTS")
                    await self.aiogtts.write_to_fp(line, buffer)

        buffer.seek(0)

        voice_guild = channel.guild
        if voice_guild is not None:
            voice_channel = await channel.connect()

            voice_channel.play(FFmpegPCMAudio(buffer.read(), pipe=True))

            while voice_channel.is_playing():
                await asyncio.sleep(1)

            await voice_channel.disconnect()
        else:
            await channel.send("You need to join a voice channel first!")
