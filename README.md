# Discord Bot Template

A template for future Discord bots using [discord.py](https://github.com/Rapptz/discord.py).

## Setup

1. Fork this repo.
2. Install Python 3.6 or higher.
3. Install Discord.py (rewrite):

```sh
pip install --user discord.py
```

4. Create a file `data/config.json` with the following contents:

```json
{
    "daemon": false,
    "dev": true,
    "token": "<bot_token>",
    "prefix": "!",
    "github_email": "<user_email>@users.noreply.github.com",
    "author": "<your_name>",
    "author_link": "<your_link>",
    "github_repo": "<your_name>/Discord-Bot-Template"
}
```

(Obviously adjust parameters as appropriate.)

5. Run `python3 main.py` to start the bot.
