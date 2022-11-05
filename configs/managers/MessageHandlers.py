from typing import Union

import discord


async def sendEphemeral(ctx, msg: Union[str, discord.Embed]):
    if isinstance(msg, str):
        await ctx.respond(msg, ephemeral=True)
    else:
        await ctx.respond(embed=msg, ephemeral=True)


def createMessageEmbed(msg):
    return discord.Embed(
        title=f"{msg}",
        colour=discord.Colour.blurple()
    )
