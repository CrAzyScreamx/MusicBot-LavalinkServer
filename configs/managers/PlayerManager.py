import datetime as dt
import random
from typing import Any
import re

import discord
import validators
import wavelink
from discord.ext import tasks
from discord.ext.pages import Page, Paginator
from wavelink import YouTubeTrack, YouTubePlaylist, SoundCloudTrack, Track
from wavelink.ext.spotify import SpotifyTrack, SpotifySearchType

from configs.managers.AnnotationChecks import sendErrorEmbed
from configs.managers.MessageHandlers import createMessageEmbed


class PlayerManager(wavelink.Player):

    def __init__(self, ctx):
        super(PlayerManager, self).__init__()

        self.ctx = ctx
        self.loop = False
        self.loopSong = False
        self._curr = None

        self.goBack = False

    @property
    def curr(self) -> Track:
        return self._curr

    @tasks.loop()
    async def player(self):
        if not self.is_playing() and not self.is_paused():
            self.player.stop()

    @player.before_loop
    async def player_before(self):
        if self.goBack:
            self.goBack = False
            self.queue.put_at_front(self.queue.history.pop())
            self._curr = self.queue.history.pop()
            self.queue.history.put(self.curr)
        elif self._curr is None or not self.loopSong:
            self._curr = self.queue.get()

        await self.ctx.send(embed=self.songProps())
        await self.play(source=self._curr)

    @player.after_loop
    async def player_after(self):
        if self.queue.is_empty and not self.goBack:
            if not self.loop:
                self.cleanup()
                await self.disconnect()
                return
            print(self.queue.history)
            while not self.queue.history.is_empty:
                self.queue.put(self.queue.history.pop())
            print(self.queue.history)

        self.player.restart()

    async def searchAndPlay(self, search: str, ctx) -> bool:
        results = await self._searchSongs(search)
        self.queue.__iadd__(results)

        if not self.player.is_running():
            self.player.start()
        elif isinstance(results, list):
            await ctx.followup.send(embed=createMessageEmbed(f"Enqueued ``{len(results)}`` songs"), ephemeral=True)
        elif results is not None:
            await ctx.followup.send(embed=createMessageEmbed(f"Enqueued ``{results.title}``"), ephemeral=True)
        else:
            await sendErrorEmbed(ctx, "Unsupported URL/Search")
        return True

    @staticmethod
    async def _searchSongs(search: str):
        results = None
        if not validators.url(search):
            results = await YouTubeTrack.search(query=search, return_first=True)
        elif search.startswith("https://www.youtube.com/playlist"):
            results = await YouTubePlaylist.search(query=search)
            results = results.tracks
        elif search.startswith("https://www.youtube.com/watch"):
            timeTrack = search.split("&t=")
            if len(timeTrack) == 2:
                search = timeTrack[0]
            results = await YouTubeTrack.search(query=search, return_first=True)
        elif search.startswith("https://open.spotify.com/track/"):
            results = await SpotifyTrack.search(query=search, return_first=True)
        elif search.startswith("https://open.spotify.com/playlist/"):
            results = await SpotifyTrack.search(query=search, type=SpotifySearchType.playlist)
        elif search.startswith("https://open.spotify.com/album/"):
            results = await SpotifyTrack.search(query=search, type=SpotifySearchType.album)
        elif search.startswith("https://soundcloud.com/"):
            results = await wavelink.NodePool.get_node().get_tracks(cls=SoundCloudTrack, query=search)
        return results

    def resetPlayer(self):
        self.loop = False
        self.loopSong = False
        self.queue.clear()
        self.queue.history.clear()

    def clearQueue(self) -> bool:
        self.queue.reset()
        return bool(self.queue.is_empty)

    def deleteSong(self, position: int) -> tuple[bool, Any]:
        if position < 2 or position > self.queue.count:
            return False, None
        position -= 2
        song = self.queue.__getitem__(position)
        self.queue.__delitem__(position)
        return True, song

    def shuffleQueue(self):
        random.shuffle(self.queue)

    async def skipSong(self) -> Track:
        self.loopSong = False
        item = self._curr
        await self.stop()
        return item

    async def seekTo(self, hours: int, minutes: int, seconds: int) -> None:
        pos = ((hours * 3600) + (minutes * 60) + seconds) * 1000
        if pos / 1000 > self.curr.duration:
            return None
        await self.seek(position=pos)
        return self._removeMs(dt.timedelta(seconds=pos / 1000))

    async def prevSong(self) -> Track:
        self.loopSong = False
        prevSong = self._curr
        if self.queue.history.count == 1:
            await self.seek(0)
        else:
            self.goBack = True
            await self.stop()
        return prevSong

    def removeDupes(self):
        newQueue = {self._curr.uri: self._curr}
        for i in range(self.queue.count):
            item = self.queue.__getitem__(i)
            if item.uri not in newQueue.keys():
                newQueue[item.uri] = item
        newQueue.pop(self._curr.uri)
        self.queue.clear()
        self.queue.__iadd__(list(newQueue.values()))

    def getQueuePaginator(self) -> Paginator:
        PAGE_BREAK = 4
        listOfPages = []
        currList = [self.createEmbed(self._curr, 1)]
        for i in range(self.queue.count):
            item = self.queue.__getitem__(i)
            currList.append(self.createEmbed(item, i + 2))
            if len(currList) % PAGE_BREAK and len(currList) >= PAGE_BREAK:
                listOfPages.append(currList.copy())
                currList.clear()
        listOfPages.append(currList)
        return Paginator(pages=[Page(embeds=embeds) for embeds in listOfPages])

    @staticmethod
    def createEmbed(track: Track, songNumber) -> discord.Embed:
        embed = discord.Embed(
            title=track.title,
            description=f"{songNumber} in queue",
            colour=discord.Colour.blurple()
        )
        embed.set_author(name=f"Published by {track.author}")
        if track.info['sourceName'] != 'soundcloud':
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.uri.split('=')[1]}/hqdefault.jpg")
        else:
            embed.set_thumbnail(url="https://play-lh.googleusercontent.com/lvYCdrPNFU0Ar_lXln3JShoE-NaYF_V"
                                    "-DNlp4eLRZhUVkj00wAseSIm-60OoCKznpw")
        return embed

    def songProps(self, footer=None):
        embed = discord.Embed(
            title=f"Now playing ``{self.curr.title}``",
            colour=discord.Colour.blurple()
        )
        embed.set_author(name=f"Published By {self.curr.author}")
        if self._curr.info['sourceName'] != 'soundcloud':
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{self._curr.uri.split('=')[1]}/hqdefault.jpg")
        else:
            embed.set_thumbnail(url="https://play-lh.googleusercontent.com/lvYCdrPNFU0Ar_lXln3JShoE-NaYF_V"
                                    "-DNlp4eLRZhUVkj00wAseSIm-60OoCKznpw")
        embed.set_footer(text="" if footer is None else footer)
        embed.add_field(name="ㅤ", value=self.lengthToLine())

        return embed

    def lengthToLine(self) -> str:
        AMOUNT = 25  # number of '-' as a character
        BREAK_AT = self.curr.duration / AMOUNT
        counter = 0
        amount = 0
        sentence = f"{self._removeMs(dt.timedelta(seconds=self.position))} ║"
        last_pos = self.position
        while counter < last_pos:
            sentence += "═"
            counter += BREAK_AT
            amount += 1
        while amount != AMOUNT:
            sentence += "─"
            amount += 1
        sentence += f"║ {self._removeMs(dt.timedelta(seconds=self.curr.duration))}"
        return sentence

    @staticmethod
    def _removeMs(td):
        return td - dt.timedelta(microseconds=td.microseconds)
