from collections import OrderedDict
from discord.ext import commands
from typing import Optional
import asyncio
import discord


from constants import colors, emoji, strings
import utils


class Secrets(commands.Cog):
    """Commands for secret-keeping."""

    def __init__(self, bot):
        self.bot = bot

    secrets = OrderedDict()
    secret_message = None
    secret_lock = asyncio.Lock()
    secret_submission_lock = asyncio.Lock()

    @commands.command('hide', rest_is_raw=True)
    async def hide(self, ctx, *, secret: Optional[commands.clean_content]):
        """Hide information.
        Run this command in a server with no argument (i.e. `!hide`) to start a
        secret exchange, and then run it in a DM with a secret message (e.g.
        `!hide I play 'scissors'`). Click the :eye: to reveal everyone's secret
        messages.
        Secret exchanges time out after two minutes, and there can only be one
        active exchange at a time (even across different guilds/channels).
        """
        if isinstance(ctx.channel, discord.DMChannel):
            if secret:
                await self.record_secret(ctx, secret)
                await ctx.message.add_reaction(emoji.SUCCESS)
            else:
                raise commands.UserInputError("You must specify a secret")
        else:
            if secret:
                raise commands.UserInputError("Do not type your secret message into the server channel")
            elif self.secret_lock.locked():
                await ctx.send(embed=discord.Embed(
                    color=colors.ERROR,
                    title="A secret exchange is already in progress",
                    description="Try ending that or waiting for it to end.",
                ))
            else:
                await self.start_secret(ctx)

    async def record_secret(self, ctx, secret: str):
        async with self.secret_submission_lock:
            if self.secret_message:
                self.secrets[ctx.author.id] = (secret)
                await self.update_secret_message()
            else:
                await ctx.send(embed=discord.Embed(
                    color=colors.ERROR,
                    title="No secret exchange is in progress",
                    description="Try starting one by entering this command into a guild or group chat.",
                ))

    async def update_secret_message(self):
        embed = discord.Embed(
            color=colors.ASK,
            title="Secret exchange",
            description=f"DM {self.bot.user.mention} with `{self.bot.command_prefix}hide <secret_info\N{HORIZONTAL ELLIPSIS}>`.",
        )
        if self.secrets:
            get_member = self.secret_message.guild.get_member
            mentions = (get_member(member_id).mention for member_id in self.secrets)
            embed.add_field(
                name="Respondents",
                value="\n".join(mentions)
            )
        await self.secret_message.edit(embed=embed)

    async def start_secret(self, ctx):
        async with self.secret_lock:
            self.secret_message = await ctx.send(embed=discord.Embed(
                color=colors.TEMPORARY,
                title="Preparing secret exchange\N{HORIZONTAL ELLIPSIS}",
            ))
            await self.update_secret_message()
            emojis = [emoji.REVEAL, emoji.CANCEL]
            async with utils.discord.TransientMessageReact(self.secret_message, emojis):
                try:
                    response_type, response = await utils.discord.wait_for_response(
                        ctx, self.secret_message,
                        lambda msg: msg.content in strings.CANCEL_MSGS,
                        lambda reaction, user: reaction.emoji in emojis,
                        timeout=120,
                    )
                except asyncio.TimeoutError:
                    async with self.secret_submission_lock:
                        await self.secret_message.edit(embed=discord.Embed(
                            color=colors.TIMEOUT,
                            title="Secret exchange timed out",
                        ))
                        self.secrets = OrderedDict()
                        self.secret_message = None
                        return
            async with self.secret_submission_lock:
                if response_type == 'reaction' and response.emoji == emoji.REVEAL:
                    description = ''
                    get_member = ctx.guild.get_member
                    for member_id, secret in self.secrets.items():
                        description += f"{get_member(member_id).mention}: {secret}\n"
                    await utils.discord.send_split_embed(ctx, discord.Embed(
                        color=colors.SUCCESS,
                        title="Secret exchange completed",
                        description=description,
                    ))
                else:
                    await self.secret_message.edit(embed=discord.Embed(
                        color=colors.CANCEL,
                        title="Secret exchange cancelled",
                    ))
                self.secrets = OrderedDict()
                self.secret_message = None


def setup(bot):
    bot.add_cog(Secrets(bot))
