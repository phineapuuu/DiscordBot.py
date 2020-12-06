from discord.ext import commands
from typing import Optional
import random
import re


from cogs.general import invoke_command_help
import utils


MAX_RAND = 50


class Random(commands.Cog):
    """Commands for generating random numbers."""

    def __init__(self, bot):
        self.bot = bot

    async def too_much(self, ctx, times: int):
        """Tell the user not to generate so many random numbers."""
        await ctx.send(f"_Chill._ I don't want to generate {times} random numbers; that's a lot. {MAX_RAND} is my limit.")

    @commands.group('random', aliases=['rand'])
    async def random(self, ctx, limit: Optional[int], times: Optional[int] = 1):
        """Generate a random integer.
        Example: `!random 10 3` generates two random integers from `1` to `10`.
        `limit` must be at least `1`. `times` is optional; if specified, it must
        be at least `1`.
        """
        if ctx.invoked_subcommand is None:
            if limit and limit >= 1:
                if times > MAX_RAND:
                    await self.too_much(ctx, times)
                    return
                await ctx.send(utils.human_list(
                    f"{random.randint(1, limit)}" for _ in range(times)
                ))
            else:
                await invoke_command_help(ctx)

    @random.command('percent', aliases=['%'])
    async def random_percent(self, ctx, times: Optional[int] = 1):
        """Generate a random percentage to two decimal places.
        Example: `!random % 4` genrates four random percentages.
        `times` is optional; if specified, it must be at least `1`.
        """
        if times < 1:
            await invoke_command_help(ctx)
            return
        if times > MAX_RAND:
            await self.too_much(ctx, times)
            return
        # Use random.uniform() instead of random.random() so that 100% is
        # (hopefully) included in the distribution.
        await ctx.send(utils.human_list(
            f"{random.uniform(0, 100):.2f}%" for _ in range(times)
        ))

    @commands.command('percent', aliases=['%'])
    async def random_percent2(self, ctx, times: Optional[int] = 1):
        """Generate a random percentage to two decimal places. See `random percent`."""
        await ctx.invoke(self. random_percent, times)

    dice_term_pattern = re.compile(r'(?P<rolls>\d*)d(?P<faces>\d+)(\*(?P<multiplier>\d+))?')
    mod_term_pattern = re.compile(r'\d+')

    @commands.command('roll', rest_is_raw=True)
    async def roll(self, ctx, *, dice_expressions: str):
        """Roll one or more dice, using [dice notation](https://en.wikipedia.org/wiki/Dice_notation).
        A single die roll is written as `d<sides>`; e.g. `d6`. Any number of
        sides can be used; e.g. `d273` is valid. This can be preceded by a
        number of dice to be rolled; e.g. `2d8` rolls two 8-sided dice and adds
        the result.
        One or more rolls of the same type can be multiplied by a constant
        amount with `*<multiplier>`; e.g. `2d4*5` rolls two 4-sided dice and
        then multiplies the result by 5.
        Modifiers are specified with `+<mod>` or `-<mod>`; this adds or
        subtracts a constant amount from the result. E.g. `d4+1` rolls a 4-sided
        die and then adds `1`.
        Thus, the full formula for one "term" of a dice expression is
        `[rolls]d<faces>(*<multiplier>)(±<modifier>)`. These terms can be linked
        with `+` or `-`.
        You can roll multiple sets of dice in one command as well.
        All numbers used in dice rolls must be integers.
        Example: `!roll d12 2d6+d12-3 d4*3`
        """
        if not dice_expressions:
            await invoke_command_help(ctx)
            return
        message = ''
        for dice_expression in dice_expressions.split():
            remaining = dice_expression
            first = True
            total = 0
            while remaining:
                multiplier = 1
                if remaining[0] in '+-':
                    if remaining[0] == '-':
                        multiplier = -1
                    remaining = remaining[1:]
                elif not first:
                    raise commands.UserInputError(f"Missing delimiter before `{remaining}`")
                first = False
                dice_match = self.dice_term_pattern.match(remaining)
                mod_match = self.mod_term_pattern.match(remaining)
                if dice_match:
                    rolls = int(dice_match['rolls'] or '1')
                    if rolls < 1:
                        raise commands.UserInputError(f"Invalid roll count: `{dice_match['rolls']}` at start of `{remaining}`")
                    faces = int(dice_match['faces'] or '1')
                    if faces < 2:
                        raise commands.UserInputError(f"Invalid face count: `{dice_match['faces']}` at start of `{remaining}`")
                    multiplier *= int(dice_match['multiplier'] or '1')
                    total += sum(random.randint(1, faces) for _ in range(rolls)) * multiplier
                    remaining = remaining[dice_match.end():]
                elif mod_match:
                    total += int(mod_match.group()) * multiplier
                    remaining = remaining[mod_match.end():]
                else:
                    raise commands.UserInputError(f"Cannot match dice term at start of `{remaining}`")
            message += f"`{dice_expression}` → {total}\n"
        if message.count('\n') > 1:
            message = "Rolls:\n" + message
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Random(bot))
