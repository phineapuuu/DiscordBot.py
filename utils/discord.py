from discord.ext import commands
from typing import Callable, List, Tuple
import asyncio
import discord

from constants import colors, emoji, strings


# https://birdie0.github.io/discord-webhooks-guide/other/field_limits.html
MAX_EMBEDS = 10
MAX_EMBED_FIELDS = 25
MAX_EMBED_VALUE = 1024
MAX_EMBED_TOTAL = 6000


def fake_mention(user):
    return f"{user.name}#{user.discriminator}"


MESSAGE_LINK_FORMAT = 'https://discordapp.com/channels/{guild.id}/{channel.id}/{message_id}'


def get_message_link(message: discord.Message):
    return MESSAGE_LINK_FORMAT.format(message.guild, message.channel, message.id)


def embed_happened_footer(past_participle: str, user: discord.abc.User):
    return {
        'text': f"{past_participle} by {fake_mention(user)}",
        'icon_url': user.avatar_url,
    }


def _split_text(p: str, max_len: int) -> Tuple[str, str]:
    """Split text given some maximum length.
    This function will try to split at paragraph boundaries ('\n\n'), then at
    linebreaks ('\n'), then at spaces (' '), and at a last resort between words.
    """
    if len(p) < max_len:
        return p, None
    i = p.rfind('\n\n', 0, max_len)
    if i == -1:
        i = p.rfind('\n', 0, max_len)
    if i == -1:
        i = p.rfind(' ', 0, max_len)
    if i == -1:
        i = max_len - 1
    return p[:i], p[i:].strip()


def split_embed(embed: discord.Embed) -> List[discord.Embed]:
    """Split an embed as needed in order to avoid hitting Discord's size limits.
    Inline fields that are too long will be made non-inline.
    """
    description = embed.description
    empty_embed = discord.Embed(color=embed.color)
    embeds = [discord.Embed(color=embed.color, title=embed.title)]
    while description:
        embeds[-1].description, description = _split_text(description, 2048)
        embeds.append(empty_embed.copy())
    length = len(embed.title) + len(embed.description)
    # TODO test handling of description
    field_stack = [{
        'name': field.name.strip(),
        'value': field.value.strip(),
        'inline': field.inline,
        'continued': False,
    } for field in reversed(embed.fields)]
    if not field_stack:
        del embeds[-1]
    while field_stack:
        field = field_stack.pop()
        name = field['name']
        value = field['value']
        if value and len(value) >= MAX_EMBED_VALUE:
            former, latter = _split_text(value, MAX_EMBED_VALUE)
            # This is a LIFO stack, so push the latter field first.
            field_stack.append({
                'name': name,
                'value': latter,
                'inline': False,
                'continued': True,
            })
            field_stack.append({
                'name': name,
                'value': former,
                'inline': False,
                'continued': field['continued']
            })
        else:
            field_length = len(name or '') + len(value or '')
            length += field_length
            too_many_fields = len(embeds[-1].fields) >= MAX_EMBED_FIELDS
            # Subtract footer and some extra wiggle room
            too_big_embed = length >= MAX_EMBED_TOTAL - len(embed.footer) - 10
            if too_many_fields or too_big_embed:
                embeds.append(empty_embed.copy())
                length = field_length
            if field['continued']:
                field['name'] += strings.CONTINUED
            del field['continued']
            embeds[-1].add_field(**field)
    if len(embeds) == 1:
        embeds[0].set_footer(text=embed.footer.text, icon_url=embed.footer.icon_url)
        embeds[0].url = embed.url
        embeds[0].timestamp = embed.timestamp
    else:
        if embed.footer:
            footer_icon_url = embed.footer.icon_url
            footer_text = embed.footer.text + f" ({{}}/{len(embeds)})"
        else:
            footer_icon_url = embed.footer.icon_url
            footer_text = f"{{}}/{len(embeds)}"
        for i, new_embed in enumerate(embeds):
            new_embed.set_footer(
                text=footer_text.format(i + 1),
                icon_url=footer_icon_url,
            )
            new_embed.url = embed.url
            new_embed.timestamp = embed.timestamp
    return embeds


async def send_split_embed(ctx: commands.Context, big_embed: discord.Embed, *, typing: bool = True):
    embeds = split_embed(big_embed)
    if typing and len(embeds) > 1:
        async with ctx.typing():
            for embed in embeds[:-1]:
                await ctx.send(embed=embed)
        await ctx.send(embed=embeds[-1])
    else:
        for embed in embeds:
            await ctx.send(embed=embed)


async def safe_bulk_delete(messages: List[discord.Message]):
    for i in range(1, len(messages), 100):
        batch = messages[i:i + 100]
        try:
            await batch[0].channel.delete_messages(batch)
        except discord.HTTPException:
            for m in batch:
                await m.delete()


async def wait_for_response(ctx: commands.Context,
                            m: discord.Message,
                            message_check: Callable[[discord.Message], bool],
                            reaction_check: Callable[[discord.Reaction, discord.abc.User], bool],
                            *,
                            timeout: int):
    """Wait for either a reaction to m by ctx.author or a message by ctx.author
    in the same channel as m.
    Returns a tuple (response_type, response), where response_type is either
    'message' or 'reaction' and response is the discord.Message or
    discord.Reaction object itself.
    Throws asyncio.TimeoutError if a timeout occurs.
    """
    pending = ()
    try:
        # Wait for either ...
        done, pending = await asyncio.wait([
            # ... a message containing, e.g. '!y', ...
            ctx.bot.wait_for(
                'message',
                check=lambda msg: (
                    msg.channel == ctx.channel
                    and msg.author == ctx.author
                    and message_check(msg)
                ),
                timeout=timeout,
            ),
            # ... or a reaction.
            ctx.bot.wait_for(
                'reaction_add',
                check=lambda reaction, user: (
                    reaction.message.id == m.id
                    and user == ctx.author
                    and reaction_check(reaction, user)
                ),
                timeout=timeout,
            )
        ], return_when=asyncio.FIRST_COMPLETED)
        result = done.pop().result()
        if isinstance(result, discord.Message):
            return 'message', result
        else:
            return 'reaction', result[0]
    finally:
        # Cancel anything that didn't complete.
        for future in pending:
            future.cancel()


class TransientMessageReact:
    """An async context manager that places emojis on a message and then removes
    them at the end."""

    def __init__(self, m, emojis):
        self.m = m
        self.emojis = emojis

    async def __aenter__(self):
        for e in self.emojis:
            await self.m.add_reaction(e)

    async def __aexit__(self, exc_type, exc_value, traceback):
        for e in self.emojis:
            await self.m.remove_reaction(e, self.m.guild.me)


async def get_confirm(ctx, m, *, timeout=30):
    """Recieve a yes/no response to a message via reaction or a message.
    Returns 'y' for an affirmative response, 'n' for a negative response, and
    't' for a timeout.
    """
    emojis = [emoji.CONFIRM, emoji.CANCEL]
    async with TransientMessageReact(m, emojis):
        try:
            response_type, response = await wait_for_response(
                ctx,
                m,
                lambda msg: msg.content in strings.CONFIRM_MSGS + strings.CANCEL_MSGS,
                lambda reaction, user: reaction.emoji in emojis,
                timeout=timeout
            )
            if response_type == 'message':
                return 'y' if response.content in strings.CONFIRM_MSGS else 'n'
            if response_type == 'reaction':
                return 'y' if response.emoji == emoji.CONFIRM else 'n'
        except asyncio.TimeoutError:
            return 't'


async def get_confirm_embed(ctx, *, timeout: int = 30, **kwargs):
    """Send an embed and call `get_confirm()`.
    Returns a tuple (message, response).
    All keyword arguments (besides timeout) are passed to discord.Embed().
    """
    m = await ctx.send(embed=discord.Embed(color=colors.ASK, **kwargs))
    return (m, await get_confirm(ctx, m, timeout=timeout))


async def query_content(ctx, *, timeout: int = 30, allow_file: bool = False, clean_content: bool = False, **kwargs):
    """Send an embed and query the user for content.
    Returns a tuple (message, response, content), where response is 'y', 'n', or
    't', and content is either a string (if response == 'y') or None.
    All keyword arguments (besides timeout) are passed to discord.Embed().
    """
    m = await ctx.send(embed=discord.Embed(color=colors.ASK, **kwargs))
    async with TransientMessageReact(m, emoji.CANCEL):
        try:
            response_type, response = await wait_for_response(
                ctx,
                m,
                lambda msg: True,
                lambda reaction, user: reaction.emoji == emoji.CANCEL,
                timeout=timeout,
            )
            if response_type == 'message':
                if clean_content:
                    content = response.clean_content.strip()
                else:
                    content = response.content.strip()
                if response.attachments and allow_file:
                    content = (await response.attachments[0].read()).decode().strip()
            if (response_type == 'reaction' or content.startswith(ctx.prefix) or not content):
                return m, 'n', None
            return m, 'y', content
        except asyncio.TimeoutError:
            return m, 't', None


async def edit_embed_for_response(m, response, *, title_format, **kwargs):
    """Edit a message, changing the color and title according to a user response
    (either 'y', 'n', or 't').
    All keyword arguments (besides title_format) are passed to discord.Embed().
    """
    await m.edit(embed=discord.Embed(
        color=colors.YESNO[response],
        title=title_format.format(strings.YESNO[response]),
        **kwargs
    ))


async def is_admin(ctx):
    if await ctx.bot.is_owner(ctx.author):
        return True
    try:
        if ctx.author.guild_permissions.administrator:
            return True
    except AttributeError:
        pass
    return False


async def invoke_command(ctx, command_name_to_invoke, *args, **kwargs):
    await ctx.invoke(ctx.bot.get_command(command_name_to_invoke), *args, **kwargs)


def sort_users(user_list):
    def key(user):
        if isinstance(user, discord.abc.User):
            return user.display_name.lower()
        else:
            return user
    return sorted(user_list, key=key)


def print_embed(embed):
    print()
    print(f"BEGIN EMBED (length {len(embed)})")
    for attr in ('title', 'type', 'description', 'url', 'timestamp', 'color'):
        print(f"  {attr}={getattr(embed, attr)!r}")
    print("  fields=[")
    for field in embed.fields:
        print(repr(field))
    print("  ]")
    print("END EMBED")
    print()


class MeOrMemberConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if argument == 'me':
            return ctx.author
        return await commands.MemberConverter().convert(ctx, argument)
