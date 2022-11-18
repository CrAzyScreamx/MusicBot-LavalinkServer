import os

import discord
from dotenvy import read_file, load_env

load_env(read_file("configs/systemFiles/args.env"))

bot = discord.Bot(description="Music bot to fulfill your needs", intents=discord.Intents.all())


if __name__ == "__main__":
    bot.load_extension("cogs")
    bot.run(os.getenv("DEV_TOKEN"))
