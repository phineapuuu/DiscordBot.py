from discord.ext import commands
import discord

from utils import l
from utils.discord import invoke_command
from constants import colors, info, strings


async def invoke_command_help(ctx):
    await invoke_command(ctx, 'help', command_name=ctx.command.qualified_name)


def get_command_signature(command):
    # This is almost entirely copied from within discord.ext.commands, but
    # discord.ext.commands's function ignores aliases.
    result = command.qualified_name
    if command.usage:
        result += " " + command.usage
    elif command.clean_params:
        result = command.qualified_name
        params = command.clean_params
        if params:
            for name, param in command.clean_params.items():
                if param.default is not param.empty:
                    if param.default not in (None, ''):
                        result += f" [{name}={param.default}]"
                    else:
                        result += f" [{name}]"
                elif param.kind == param.VAR_POSITIONAL:
                    result += f" [{name}\N{HORIZONTAL ELLIPSIS}]"
                else:
                    result += f" <{name}>"
    return result


class General(commands.Cog):
    """General-purpose commands."""

    def __init__(self, bot):
        self.bot = bot
        bot.original_help = bot.get_command('help')
        bot.remove_command('help')

    def __unload(self):
        self.bot.add_command(self.bot.original_help)

    @commands.command()
    async def ping(self, ctx):
        """Ping the bot."""
        await ctx.send("Pong!")

    # TODO: use discord.ext.commands.HelpCommand instead
    @commands.command(aliases=['h', 'man'])
    async def help(self, ctx, *, command_name: str = None):
        """Display a list of all commands or display information about a specific command."""
        if command_name:
            command = self.bot.get_command(command_name)
            if command is None:
                await ctx.send(embed=discord.Embed(
                    color=colors.ERROR,
                    title="Command help",
                    description=f"Could not find command `{command_name}`.",
                ))
            elif await command.can_run(ctx):
                embed = discord.Embed(
                    color=colors.HELP,
                    title="Command help",
                    description=f"`{command.name}`",
                )

                if command.usage or command.clean_params:
                    embed.add_field(
                        name="Synopsis",
                        value=f"`{get_command_signature(command)}`",
                    )
                if command.aliases:
                    aliases = ', '.join(f"`{alias}`" for alias in command.aliases)
                    embed.add_field(
                        name="Aliases",
                        value=aliases,
                    )
                if command.help:
                    embed.add_field(
                        name="Description",
                        value=command.help,
                        inline=False,
                    )
                if hasattr(command, 'commands'):
                    subcommands = []
                    for subcommand in command.commands:
                        s = f"`{get_command_signature(subcommand)}`"
                        if subcommand.short_doc:
                            s += f" \N{EM DASH} {subcommand.short_doc}"
                        subcommands.append(s)
                    subcommands.sort()
                    embed.add_field(
                        name="Subcommands",
                        value="\n".join(subcommands) or strings.EMPTY_LIST,
                        inline=False,
                    )
                misc = ''
                if not command.enabled:
                    misc += "This command is currently disabled.\n"
                if command.hidden:
                    misc += "This command is usually hidden.\n"
                if misc:
                    embed.add_field(
                        name="Miscellaneous",
                        value=misc,
                        inline=False,
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(
                    color=colors.ERROR,
                    title="Command help",
                    description=f"You have insufficient permission to access `{command_name}`.",
                ))
        else:
            cog_names = []
            for command in self.bot.commands:
                if command.cog_name:
                    if command.cog_name not in cog_names:
                        cog_names.append(command.cog_name)
                else:
                    l.warning("Command {command.name!r} has no cog, so it will not be listed by the 'help' command")
            embed = discord.Embed(
                color=colors.HELP,
                title="Command list",
                description=f"Invoke a command by prefixing it with `{ctx.prefix}`. Use `{ctx.prefix}{ctx.command.name} [command]` to get help on a specific command.",
            )
            for cog_name in sorted(cog_names):
                lines = []
                cog = self.bot.get_cog(cog_name)
                for command in sorted(cog.get_commands(), key=lambda cmd: cmd.name):
                    if not command.hidden and (await command.can_run(ctx)):
                        line = f"\N{BULLET} **`{get_command_signature(command)}`**"
                        if command.short_doc:
                            line += f" \N{EM DASH} {command.short_doc}"
                        lines.append(line)
                if lines:
                    if hasattr(cog, 'name'):
                        name = cog.name
                    else:
                        name = cog_name
                    embed.add_field(name=name, value="\n".join(lines), inline=False)
            await ctx.send(embed=embed)

    @commands.command(aliases=['i', 'info'])
    async def about(self, ctx):
        """Display information about the bot."""
        await ctx.send(
            embed=discord.Embed(
                color=colors.INFO,
                title=f"About {info.NAME}",
                description=info.ABOUT_TEXT,
                footer_text=f"{info.NAME} v{info.VERSION}",
            ).add_field(
                name="Author",
                value=f"[{info.AUTHOR}]({info.AUTHOR_LINK})",
            ).add_field(
                name="GitHub repository",
                value=info.GITHUB_REPO_LINK,
            ).set_footer(text=f"{info.NAME} v{info.VERSION}")
        )

    @commands.command('confirm', aliases=['y', 'yes'])
    async def confirm(self, ctx):
        """Confirm a pending query."""
        pass

    @commands.command('cancel', aliases=['n', 'no'])
    async def cancel(self, ctx):
        """Cancel a pending query."""
        pass


def setup(bot):
    bot.add_cog(General(bot))
