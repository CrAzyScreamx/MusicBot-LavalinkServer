import discord
import wavelink
from discord.ext.commands import check


def isAuthorConnected():
    async def predicate(ctx):
        if not ctx.author.voice or ctx.author.voice.channel is None:
            await sendErrorEmbed(ctx, "You must be connected to a voice channel")
            return False
        return True

    return check(predicate)


def isBotConnected():
    async def predicate(ctx):
        if ctx.voice_client is None:
            await sendErrorEmbed(ctx, "Bot is not connected to any channel")
            return False
        return True

    return check(predicate)


def isBotDisconnected():
    async def predicate(ctx):
        if ctx.voice_client is not None:
            await sendErrorEmbed(ctx, "Bot is already connected to a channel")
            return False
        return True

    return check(predicate)


def inSameChannel():
    async def predicate(ctx):
        if ctx.voice_client.channel != ctx.author.voice.channel:
            await sendErrorEmbed(ctx, "The bot is not in your channel")
            return False
        return True

    return check(predicate)


def isBotPlaying():
    async def predicate(ctx):
        if not wavelink.NodePool.get_node().get_player(ctx.guild).is_playing():
            await sendErrorEmbed(ctx, "Bot is not playing anything")
            return False
        return True

    return check(predicate)


def isBotPaused():
    async def predicate(ctx):
        if not wavelink.NodePool.get_node().get_player(ctx.guild).is_paused():
            await sendErrorEmbed(ctx, "Bot is not paused")
            return False
        return True

    return check(predicate)


async def sendErrorEmbed(ctx, msg: str):
    embed = discord.Embed(
        title=f"❌ ERROR: {msg}",
        colour=discord.Colour.from_rgb(0, 0, 0)
    )
    await ctx.respond(embed=embed, ephemeral=True)
