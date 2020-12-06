from discord.ext import commands
import discord
import traceback

from . import l
from constants import colors, info


async def on_command_error(ctx, exc, *args, **kwargs):
    command_name = ctx.command.qualified_name if ctx.command else "unknown command"
    l.error(f"{str(exc)!r} encountered while executing command {command_name!r} (args: {args}; kwargs: {kwargs})")
    if isinstance(exc, commands.UserInputError):
        if isinstance(exc, commands.MissingRequiredArgument):
            description = f"Missing required argument `{exc.param.name}`."
        elif isinstance(exc, commands.TooManyArguments):
            description = "Too many arguments."
        elif isinstance(exc, commands.BadArgument):
            description = f"Bad argument:\n```\n{str(exc)}\n```"
        elif exc.args:
            description = exc.args[0]
        else:
            description = "Bad user input."
        description += f"\n\nRun `{info.COMMAND_PREFIX}help {command_name}` to view the required arguments."
    elif isinstance(exc, commands.CommandNotFound):
        # description = f"Could not find command `{ctx.invoked_with.split()[0]}`."
        return
    elif isinstance(exc, commands.CheckFailure):
        if isinstance(exc, commands.NoPrivateMessage):
            description = "Cannot be run in a private message channel."
        elif isinstance(exc, commands.MissingPermissions) or isinstance(exc, commands.BotMissingPermissions):
            if isinstance(exc, commands.MissingPermissions):
                description = "You don't have permission to do that."
            elif isinstance(exc, commands.BotMissingPermissions):
                description = "I don't have permission to do that."
            missing_perms = "\n".join(exc.missing_perms)
            description += f" Missing:\n```\n{missing_perms}\n```"
        else:
            # description = "Command check failed."
            return
    elif isinstance(exc, commands.DisabledCommand):
        description = "That command is disabled."
    elif isinstance(exc, commands.CommandOnCooldown):
        description = "That command is on cooldown."
    else:
        description = "Sorry, something went wrong. A team of highly trained monkeys has been dispatched to deal with the situation."
        await log_error(ctx, exc.original, *args, **kwargs)
    await ctx.send(embed=discord.Embed(
        color=colors.ERROR,
        title="Error",
        description=description
    ))


async def log_error(ctx, exc, *args, **kwargs):
    if not info.DAEMON:
        for entry in traceback.format_tb(exc.__traceback__):
            for line in entry.splitlines():
                l.error(line)
        l.error('')
    else:
        embed = discord.Embed(
            color=colors.ERROR,
            title="Error",
            description=f"`{str(exc)}`",
        )
        if ctx:
            if isinstance(ctx.channel, discord.DMChannel):
                guild_name = "N/A"
                channel_name = f"DM"
            elif isinstance(ctx.channel, discord.GroupChannel):
                guild_name = "N/A"
                channel_name = f"Group with {len(ctx.channel.recipients)} members (id={ctx.channel.id})"
            else:
                guild_name = ctx.guild.name
                channel_name = f"{ctx.channel.mention}"
            user = ctx.author
            embed.add_field(
                name="Guild",
                value=guild_name,
                inline=False,
            ).add_field(
                name="Channel",
                value=channel_name,
                inline=False,
            ).add_field(
                name="User",
                value=f"{user} (A.K.A. {user.display_name})",
            ).add_field(
                name="Message content",
                value=f"{ctx.message.content}",
            )
        tb = ''.join(traceback.format_tb(exc.__traceback__))
        tb = f"```\n{tb.replace('```', '` ` `')}"
        if len(tb) > 1000:
            tb = tb[:1000] + '\n```(truncated)'
        else:
            tb += '\n```'
        embed.add_field(
            name="Args",
            value=f"```\n{repr(args)}\n```" if args else "None",
        ).add_field(
            name="Keyword args",
            value=f"```\n{repr(kwargs)}\n```" if kwargs else "None",
        ).add_field(
            name="Traceback",
            value=tb,
            inline=False,
        )
        await ctx.bot.app_info.owner.send(embed=embed)
