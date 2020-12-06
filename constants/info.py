from utils.database import get_db


CONFIG = get_db('config')

DAEMON = CONFIG.get('daemon', False)
DEV = CONFIG.get('dev', False)
TOKEN = CONFIG.get('token')
COMMAND_PREFIX = CONFIG.get('prefix', '!')

GITHUB_EMAIL = CONFIG.get('github_email')
GITHUB_REPO = CONFIG.get('github_repo')
GITHUB_REPO_LINK = f'https://github.com/{GITHUB_REPO}'

NAME = "TemplateBot"
with open('VERSION') as f:
    VERSION = f.read().strip()

DESCRIPTION = "A bot template using discord.py"

ABOUT_TEXT = f"""\
{NAME} is an open source Discord bot created using HactarCE's \
[discord.py](https://github.com/Rapptz/discord.py) bot template.
"""

AUTHOR = CONFIG.get('author', '')
AUTHOR_LINK = CONFIG.get('author_link', AUTHOR and f"https://github.com/{AUTHOR}")
