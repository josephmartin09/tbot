import os

import requests

DISCORD_URL = os.environ["DISCORD_WEBHOOK_URL"]


def discord_fmt(msg):
    """Format the message as a discord code block.

    :param str msg:
    :rtype: str
    :return: The message formated as a discord code block string
    """
    return f"```\n{msg}\n```"


def send_fmt_msg(msg):
    """Send a post request to discord."""
    payload = {
        "content": discord_fmt(msg),
    }
    requests.post(DISCORD_URL, json=payload)


def send_discord_msg(msg):
    """Send a post request to discord."""
    payload = {
        "content": msg,
    }
    requests.post(DISCORD_URL, json=payload)
