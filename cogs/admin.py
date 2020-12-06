from discord.ext import commands
from subprocess import PIPE
import asyncio
import discord

from . import get_extensions
from constants import colors, strings
from utils import l
import utils


async def reload_extensions(ctx, *extensions):
    if '*' in extensions:
        title = "Reloading all extensions"
    elif len(extensions) == 1:
        title = f"Reloading `{extensions[0]}`"
    else:
        title = "Reloading extensions"
    embed = discord.Embed(
        color=colors.INFO,
        title=title
    )
    m = await ctx.send(embed=embed)
    color = colors.SUCCESS
    description = ''
    if '*' in extensions:
        extensions = get_extensions()
    for extension in extensions:
        try:
            ctx.bot.unload_extension('cogs.' + extension)
        except commands.ExtensionNotLoaded:
            pass
        try:
            ctx.bot.load_extension('cogs.' + extension)
            description += f"Successfully loaded `{extension}`.\n"
        except (commands.ExtensionError, ImportError) as exc:
            color = colors.ERROR
            description += f"Failed to load `{extension}`.\n"
            if not isinstance(exc, ImportError):
                raise
    description += "Done."
    await m.edit(embed=discord.Embed(
        color=color,
        title=title.replace("ing", "ed"),
        description=description
    ))


class Admin(commands.Cog):
    """Admin-only commands."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await utils.discord.is_admin(ctx)

    @commands.command(aliases=['die', 'quit'])
    async def shutdown(self, ctx):
        """Shut down the bot.
        This command will ask the user for confirmation first. To bypass this, use the `shutdown!` command.
        """
        await self.shutdown_(ctx)

    @commands.command(name='shutdown!', aliases=['die!', 'q!', 'quit!'], hidden=True)
    async def shutdown_noconfirm(self, ctx):
        """Shut down the bot without asking for confirmation.
        See `shutdown` for more details.
        """
        await self.shutdown_(ctx, True)

    async def shutdown_(self, ctx, noconfirm=False):
        if noconfirm:
            response = 'y'
        else:
            m, response = await utils.discord.get_confirm_embed(
                ctx,
                title="Shutdown?",
                description="This action may be difficult to undo without phsyical or remote access to the host machine. Are you sure?",
            )
        if response == 'y':
            title = "Shutting down\N{HORIZONTAL ELLIPSIS}"
        else:
            title = f"Shutdown {strings.YESNO[response]}"
        if noconfirm:
            color = colors.INFO
        else:
            color = colors.YESNO[response]
        await (ctx.send if noconfirm else m.edit)(embed=discord.Embed(
            color=color,
            title=title
        ))
        if response == 'y':
            l.info(f"Shutting down at the command of {utils.discord.fake_mention(ctx.author)}...")
            await self.bot.logout()

    @commands.command()
    async def update(self, ctx):
        """Run `git pull` to update the bot."""
        subproc = await asyncio.create_subprocess_exec('git', 'pull', stdout=PIPE)
        embed = discord.Embed(
            color=colors.INFO,
            title="Running `git pull`"
        )
        m = await ctx.send(embed=embed)
        returncode = await subproc.wait()
        embed.color = colors.ERROR if returncode else colors.SUCCESS
        stdout, stderr = await subproc.communicate()
        if stdout:
            embed.add_field(
                name="Stdout",
                value=f"```\n{stdout.decode('utf-8')}\n```",
                inline=False,
            )
        if stderr:
            embed.add_field(
                name="Stderr",
                value=f"```\n{stderr.decode('utf-8')}\n```",
                inline=False,
            )
        if not (stdout or stderr):
            embed.description = "`git pull` completed."
        await m.edit(embed=embed)
        await utils.discord.invoke_command(ctx, 'reload *')

    @commands.command(aliases=['r'])
    async def reload(self, ctx, *, extensions: str = '*'):
        """Reload an extension.
        Use `reload *` to reload all extensions.
        This command is automatically run by `update`.
        """
        await reload_extensions(ctx, *extensions.split())


def setup(bot):
    bot.add_cog(Admin(bot))
    # cog = Admin(bot)
    # cog.admins.__docstring__ = cog.admins.__docstring__.format(bot.app_info.owner.mention)
    # bot.add_cog(cog)
