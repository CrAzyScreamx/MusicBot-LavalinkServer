import datetime as dt

from discord import option
from discord.ext import commands
from discord.ext.commands import slash_command
from wavelink import NodePool

from configs.managers.AnnotationChecks import *
from configs.managers.MessageHandlers import *
from configs.managers.PlayerManager import PlayerManager

GUILD_IDS = [757857626112655390]


class MusicCommands(commands.Cog):

    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot

    @slash_command(name="join",
                   description="Joins the channel",
                   guild_ids=GUILD_IDS)
    @isBotDisconnected()
    @isAuthorConnected()
    async def _join(self, ctx):
        await sendEphemeral(ctx, createMessageEmbed("🤠 Howdy! type /play to start playing songs!"))
        await ctx.author.voice.channel.connect(cls=PlayerManager(ctx))

    @slash_command(name="leave",
                   description="Leaves the channel",
                   guild_ids=GUILD_IDS)
    @isBotConnected()
    @isAuthorConnected()
    async def _leave(self, ctx):
        await sendEphemeral(ctx, createMessageEmbed("Okay 😭"))
        NodePool.get_node().get_player(ctx.guild).resetPlayer()
        await NodePool.get_node().get_player(ctx.guild).disconnect()

    @slash_command(name="play",
                   description="Plays a song from YT/Spotify/Soundcloud",
                   guild_ids=GUILD_IDS)
    @isAuthorConnected()
    @option(name="search", type=str, description="Paste YT/Spotify/Soundcloud link or just search")
    async def _play(self, ctx, search):
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect(cls=PlayerManager(ctx))
        player = NodePool.get_node().get_player(ctx.guild)
        await sendEphemeral(ctx, createMessageEmbed(f"🎶 Searching ``{search}`` on the web!"))
        try:
            await player.searchAndPlay(search, ctx)
        except TypeError:
            await sendErrorEmbed(ctx, "URL/Search not supported")

    @slash_command(name="pause",
                   description="Pauses the current playing song",
                   guild_ids=GUILD_IDS)
    @isBotPlaying()
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _pause(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        await player.pause()
        return await sendEphemeral(ctx, createMessageEmbed(f"⏸   Paused ``{player.curr}``"))

    @slash_command(name="resume",
                   description="Resumes the current playing song",
                   guild_ids=GUILD_IDS)
    @isBotPaused()
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _resume(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        await player.resume()
        return await sendEphemeral(ctx, createMessageEmbed(f"▶️  Resumed {player.curr}"))

    @slash_command(name="nowplaying",
                   description="Displays the current playing audio",
                   guild_ids=GUILD_IDS)
    @isBotPlaying()
    @isAuthorConnected()
    async def _nowplaying(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        return await sendEphemeral(ctx, player.songProps("Now Playing"))

    @slash_command(name="loopsong",
                   description="Loops the current Song",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _loopSong(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        player.loopSong = not player.loopSong
        if player.loopSong:
            return await sendEphemeral(ctx, createMessageEmbed("🔁 Looping Song"))
        return await sendEphemeral(ctx, createMessageEmbed("🔁 Cancelled loop"))

    @slash_command(name="clear",
                   description="Clears the current queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _clear(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        if player.clearQueue():
            return await sendEphemeral(ctx, createMessageEmbed("🧹 Cleared the queue"))
        return await sendErrorEmbed(ctx, "Error clearing the queue")

    @slash_command(name="delete",
                   description="Delete song at position x in the queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    @option(name="pos", type=int, description="Position of the song in the queue")
    async def _delete(self, ctx, pos):
        player = NodePool.get_node().get_player(ctx.guild)
        state, song = player.deleteSong(pos)
        if state:
            return await sendEphemeral(ctx, createMessageEmbed(f"🚫 Deleted ``{song.title}`` from the queue"))
        await sendErrorEmbed(ctx, f"Couldn't delete song at position ``{pos}``")

    @slash_command(name="shuffle",
                   description="Shuffles the current Queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _shuffle(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        player.shuffleQueue()
        return await sendEphemeral(ctx, createMessageEmbed("🔀 Shuffled the queue"))

    @slash_command(name="skip",
                   description="Skips the current song",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _skip(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        track = await player.skipSong()
        return await sendEphemeral(ctx, createMessageEmbed(f"⏭ Skipped song ``{track.title}``"))

    @slash_command(name="back",
                   description="Goes back to previous song",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _back(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        track = await player.prevSong()
        return await sendEphemeral(ctx, createMessageEmbed(f"⏮ Stopped ``{track.title}`` Returning to previous"))

    @slash_command(name="loopqueue",
                   description="Loop the queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _loopqueue(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        player.loop = not player.loop
        if player.loop:
            return await sendEphemeral(ctx, createMessageEmbed("🔁 Looping Queue"))
        return await sendEphemeral(ctx, createMessageEmbed("🔁 Cancelled loop"))

    @slash_command(name="removedupes",
                   description="Remove Song duplicates",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    async def _removedupes(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        player.removeDupes()
        return await sendEphemeral(ctx, createMessageEmbed("Removed all duplicated songs"))

    @slash_command(name="seek",
                   description="Seek to a current position in the queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    @inSameChannel()
    @isBotConnected()
    @isAuthorConnected()
    @option(name="hours", type=int, description="Hours of the video")
    @option(name="minutes", type=int, description="Minutes of the video")
    @option(name="seconds", type=int, description="Seconds of the video")
    async def _seek(self, ctx, hours=None, minutes=None, seconds=None):
        if hours == minutes == seconds is None:
            return await sendErrorEmbed(ctx, "You must gi.ve at least one argument! (hours, minutes, or seconds")
        hours = hours if hours is not None else 0
        minutes = minutes if minutes is not None else 0
        seconds = seconds if seconds is not None else 0
        player = NodePool.get_node().get_player(ctx.guild)
        pos = await player.seekTo(hours, minutes, seconds)
        if pos is None:
            return await sendErrorEmbed(ctx, f"You can only seek from 00:00:00 to "
                                             f"{dt.timedelta(seconds=player.curr.duration)}")
        return await sendEphemeral(ctx, createMessageEmbed(f"🔄 Seeked to position {pos}"))

    @slash_command(name="queue",
                   description="Presents the current queue",
                   guild_ids=GUILD_IDS)
    @commands.check_any(isBotPlaying(), isBotPaused())
    async def _queue(self, ctx):
        player = NodePool.get_node().get_player(ctx.guild)
        if paginator := player.getQueuePaginator():
            return await paginator.respond(ctx.interaction, ephemeral=True)
        return sendErrorEmbed(ctx, "Queue is empty")



def setup(bot):  # sourcery skip: instance-method-first-arg-name
    bot.add_cog(MusicCommands(bot))
