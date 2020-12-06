from discord.ext import commands
# import discord


# from constants import colors, strings
# from utils import l
# import nomic
# import utils


class CogName(commands.Cog):
    """Brief cog description."""

    name = "Cog name"

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(CogName(bot))
