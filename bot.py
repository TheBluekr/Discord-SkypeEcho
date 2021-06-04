import discord
import asyncio

from discord.ext import commands
from discord.utils import get

import logging
import random

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-19s | %(levelname)-8s | %(name)-16s | %(message)-s', "%d-%m-%Y %H:%M:%S")
ch.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)

discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.WARNING)

class Echo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"cog.Echo")
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Loaded cog.Echo")
        self.filelist = [["EchoStart.mp3"], ["EchoSilence.mp3"], ["EchoPost.mp3"]]
        self.channel = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.bot.user.name}")
        # I know it's hard coded, but it doesn't matter if it's only intended for only one server
        self.channel = self.bot.get_channel(544135113726754820)

    @commands.Cog.listener()
    async def on_message(self, message):
        if(message.content == "echo"):
            if(self.channel == None):
                return
            vc = get(self.bot.voice_clients, channel=self.channel)
            if(vc != None):
                return
            vc = await self.channel.connect()
            if(not vc.is_connected()):
                self.logger.error(f"Something went wrong joining voice {self.channel.name}")
                return
            await self.StartSound(vc)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if(before.channel != after.channel):
            if(after.channel != None):
                if(after.channel == self.channel):
                    await self.on_member_join(member, before, after)
            if(before.channel != None):
                if(before.channel == self.channel):
                    await self.on_member_leave(member, before, after)

    async def on_member_join(self, member, before, after):
        if(after.channel in self.bot.voice_clients): # We're already connected, ignore this case
            return

        if(len(after.channel.members) == 1):
            self.logger.info(f"{after.channel.members[0].name} just connected")
            vc = await after.channel.connect()
            if(not vc.is_connected()):
                # Something went wrong while connecting...
                self.logger.error(f"Something went wrong joining voice {after.channel.name}")
                return
            await self.StartSound(vc)

    async def on_member_leave(self, member, before, after):
        vc = get(self.bot.voice_clients, channel=before.channel)
        if(len(before.channel.members) == 1 and vc != None and after.channel == None):
            self.logger.info(f"Nobody's left in voice {before.channel.name}")
            await self.Disconnect(vc)
    
    async def StartSound(self, vc):
        # Start playing sounds from the start of our file list
        self.Playback(vc, 0)

    def Playback(self, vc, index):
        # Future proofing in case more sound files get added
        if(len(self.filelist[index]) > 1):
            randint = random.randrange(0,len(self.filelist[index])-1)
        else:
            randint = 0
        self.PlaySound(self.filelist[index][randint], vc, lambda e: self.PlaybackFinish(vc, index, randint, e))

    def PlaybackFinish(self, vc, index, randint, err):
        if(err != None):
            self.logger.error(err)
            asyncio.run_coroutine_threadsafe(self.Disconnect(vc), self.bot.loop)
            return
        if(not vc.is_connected()):
            self.logger.warning("Voice prematurely disconnected, cancelling playback")
            return
        self.logger.info(f"Succesfully finished playing {self.filelist[index][randint]}")
        if(len(self.filelist) == index+1):
            asyncio.run_coroutine_threadsafe(self.Disconnect(vc), self.bot.loop)
            return
        self.Playback(vc, index+1)
    
    async def Disconnect(self, vc):
        if(not vc.is_connected()):
            self.logger.warning("Disconnect() called while not connected")
            return
        channelName = vc.channel.name
        if(vc.is_playing() or vc.is_paused()):
            self.logger.info("Stopping playback due to disconnect")
            vc.stop()
        await vc.disconnect()
        self.logger.info(f"Disconnected from {channelName}")
    
    def PlaySound(self, path, vc, returnFunc):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"./{path}"))
        vc.play(source, after=returnFunc)
        self.logger.info(f"Playing {path} in {vc.channel.name}")

bot = commands.Bot(command_prefix="!")
bot.add_cog(Echo(bot))
bot.run("<token>")
# Time stamps
# Start 0-12s
# Silence 12-17s
# Post 17-38s