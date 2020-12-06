from datetime import datetime
from discord.ext import commands
import discord

from cogs.general import invoke_command_help
import utils


class Tests(commands.Cog):
    """Commands for testing things."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group('test', invoke_without_command=True)
    async def test_group(self, ctx):
        await invoke_command_help(ctx)

    @test_group.command('embed_split')
    async def test_embed_split(self, ctx):
        embed = discord.Embed(
            title="Every single natural number (1-999)",
            description=', '.join(map(str, range(1, 1000))),
            timestamp=datetime.fromtimestamp(utils.now()),
        ).add_field(
            name="Feild #1 (1000-1499)",
            value=', '.join(map(str, range(1000, 1500))),
        ).add_field(
            name="Field #2 (2000-2500)",
            value=', '.join(map(str, range(2000, 2500))),
        ).set_footer(
            **utils.discord.embed_happened_footer("Tested", ctx.author)
        )
        await utils.discord.send_split_embed(ctx, embed)


def setup(bot):
    bot.add_cog(Tests(bot))
