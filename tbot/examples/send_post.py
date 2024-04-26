import os

import requests
from texttable import Texttable

DISCORD_URL = os.environ["DISCORD_WEBHOOK_URL"]


def discord_fmt(msg):
    """Format the message as a discord code block.

    :param str msg:
    :rtype: str
    :return: The message formated as a discord code block string
    """
    return f"```\n{msg}\n```"


table_msg = Texttable()
table_msg.add_row(["Period", "Time", "Direction"])
table_msg.add_row(["1m", "2024-04-25 00:07:00-05:00", "SHORT"])
content = discord_fmt(table_msg.draw())

print(content)

payload = {
    "content": content,
}
resp = requests.post(DISCORD_URL, json=payload)
print(resp)
