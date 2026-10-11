import html
from aiogram.types import User as TgUser

SEP = "➖➖➖➖➖➖➖➖➖"
DOT = "▫️▫️▫️▫️▫️▫️▫️▫️▫️"


def esc(s: str | None) -> str:
    return html.escape(s or "")


def user_mention(user: TgUser | None, user_id: int | None = None, name: str | None = None) -> str:
    if user:
        return f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{esc(user.first_name)}</a>"
    if name:
        return esc(name)
    return f"<code>{user_id}</code>"


def card_symbol(c: str) -> str:
    return c