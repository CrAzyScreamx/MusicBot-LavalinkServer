import os

from discord import ApplicationContext
from discord.ext import commands
from wavelink import Node
from wavelink.errors import ZeroConnectedNodes
from wavelink.ext.spotify import SpotifyClient

from cogs.MusicCommands import GUILD_IDS
from configs.managers.AnnotationChecks import *


class Events(commands.Cog):

    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready to function, connecting Lavalink node")
        await self.connect_node()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: Node):
        await self.bot.wait_until_ready()
        print(f"node {node.identifier} is up and running")

    @commands.slash_command(name="reconnectnodes",
                            description="Reconnect Lavalink nodes in case of an error")
    @commands.check_any(commands.is_owner())
    async def _reconnect(self, ctx: ApplicationContext):
        try:
            wavelink.NodePool.get_node()
        except ZeroConnectedNodes:
            await self.connect_node()

    # Connect the node to the system
    async def connect_node(self):
        await self.__connectDebugger(os.getenv("NODE_HOST"))
        if not wavelink.NodePool.get_node().is_connected():
            print("Can't connect to the host locally, connecting to a remote node...")
            await self.__connectDebugger(os.getenv("NODE_HOST"))

    async def __connectDebugger(self, host):
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=host,
            port=int(os.getenv("NODE_PORT")),
            password=os.getenv("NODE_PASS"),
            spotify_client=SpotifyClient(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"))
        )


def setup(bot: discord.Bot):
    bot.add_cog(Events(bot))
