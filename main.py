!/usr/bin/env python3

import logging

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("Discord.py is required. See the README for instructions on installing it.")
    exit(1)

from cogs import get_extensions
from constants import colors, info
from utils import l, LOG_SEP
import utils


LOG_LEVEL_API = logging.WARNING
LOG_LEVEL_BOT = logging.INFO
LOG_FMT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"


if info.DAEMON:
    logging.basicConfig(format=LOG_FMT, filename='bot.log')
else:
    logging.basicConfig(format=LOG_FMT)
logging.getLogger('discord').setLevel(LOG_LEVEL_API)
l.setLevel(LOG_LEVEL_BOT)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=info.COMMAND_PREFIX,
            case_insensitive=True,
            description=kwargs.pop('description'),
            status=discord.Status.dnd
        )
        self.app_info = None
        self.cogs_loaded = set()

    async def ready_status(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name="Quonauts")
        )

    async def on_connect(self):
        l.info(f"Connected as {self.user}")
        await self.change_presence(status=discord.Status.idle)

    async def on_ready(self):
        self.app_info = await self.application_info()
        l.info(LOG_SEP)
        l.info(f"Logged in as: {self.user.name}")
        l.info(f"discord.py:   {discord.__version__}")
        l.info(f"Owner:        {self.app_info.owner}")
        l.info(LOG_SEP)
        await self.load_all_extensions()
        await self.ready_status()

    async def on_resumed(self):
        l.info("Resumed session.")
        await self.ready_status()

    async def load_all_extensions(self, reload=False):
        """Attempt to load all .py files in cogs/ as cog extensions.
        Return a dictionary which maps cog names to a boolean value (True =
        successfully loaded; False = not successfully loaded).
        """
        succeeded = {}
        disabled_extensions = set()
        if not info.DEV:
            disabled_extensions.add('tests')
        for extension in get_extensions(disabled=disabled_extensions):
            try:
                if reload or extension not in self.cogs_loaded:
                    self.load_extension(f'cogs.{extension}')
                    l.info(f"Loaded extension '{extension}'")
                    self.cogs_loaded.add(extension)
                    succeeded[extension] = True
            except Exception as exc:
                l.error(f"Failed to load extension {extension!r} due to {type(exc).__name__}: {exc}")
                if hasattr(exc, 'original'):
                    l.error(f"More details: {type(exc.original).__name__}: {exc.original}")
                succeeded[extension] = False
        if succeeded:
            l.info(LOG_SEP)
        return succeeded

    async def on_guild_join(self, guild):
        """This event triggers when the bot joins a guild."""
        l.info(f"Joined {guild.name} with {guild.member_count} users!")

    async def on_message(self, message):
        """This event triggers on every message received by the bot, including
        ones that it sent itself.
        """
        if message.author.bot:
            return  # Ignore all bots.
        if message.content.startswith(self.user.mention):
            prefix = info.COMMAND_PREFIX
            description = f"Hi! I'm {self.user.mention}, {info.DESCRIPTION[0].lower()}{info.DESCRIPTION[1:]}."
            description += f" Type `{prefix}help` to get general bot help, `{prefix}help <command>` to get help for a specific command, and `!about` for general info about me."
            await message.channel.send(embed=discord.Embed(
                color=colors.INFO,
                description=description,
            ))
        else:
            await self.process_commands(message)

    async def on_command_error(self, exc, *args, **kwargs):
        await utils.error_handling.on_command_error(exc, *args, **kwargs)


if __name__ == '__main__':
    bot = Bot(description=info.DESCRIPTION)
    try:
        bot.run(info.TOKEN)
    except discord.errors.LoginFailure:
        print(f"Please specify a proper bot token in {info.CONFIG.filepath}.")
        exit(1)
