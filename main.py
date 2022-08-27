# This example requires the 'message_content' intent.

import asyncio
from io import BytesIO
import discord
import logging
import os
from aiogtts import aiogTTS

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
aiogtts = aiogTTS()
io = BytesIO()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        await aiogtts.save(message.author.name, 'hello.mp3')
        voice_guild = message.guild
        if voice := message.author.voice and voice_guild is not None:
            channel = voice.channel
            voice_channel = await channel.connect()
            voice_channel.play(discord.FFmpegPCMAudio(io), after=lambda e: print('done', e))

            while voice_channel.is_playing():
                await asyncio.sleep(1)
            await voice_channel.disconnect()
        else:
            await message.channel.send('You need to join a voice channel first!')

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member == client.user:
        return

    if before.channel is not None:
        await depart_user(member, before.channel)
        
    if after.channel is not None:
        await greet_user(member)

async def greet_user(member: discord.Member):
    await say_line(f"{member.name} has joined the channel", member.voice.channel)

async def depart_user(member: discord.Member, channel: discord.VoiceChannel):
    await say_line(f"{member.name} has left the channel", channel)

async def say_line(line: str, channel: discord.VoiceChannel):
    await aiogtts.save(line, 'join.mp3')
    
    voice_guild = channel.guild
    if voice_guild is not None:
        voice_channel = await channel.connect()

        voice_channel.play(discord.FFmpegPCMAudio('join.mp3'))

        while voice_channel.is_playing():
            await asyncio.sleep(1)

        await voice_channel.disconnect()
    else:
        await channel.send('You need to join a voice channel first!')


client.run(os.environ['DISCORD_TOKEN'], log_handler=handler)
