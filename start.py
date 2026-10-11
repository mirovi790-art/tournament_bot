from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID
from database import SessionLocal
from models import User, Ban, Admin
from keyboards import main_menu_kb, owner_menu_kb, admin_menu_kb
from utils import SEP

router = Router()


async def _check_ban(user_id: int) -> bool:
    async with SessionLocal() as session:
        return await session.get(Ban, user_id) is not None


async def _upsert_user(from_user):
    async with SessionLocal() as session:
        u = await session.get(User, from_user.id)
        if u is None:
            u = User(id=from_user.id, username=from_user.username,
                     first_name=from_user.first_name)
            session.add(u)
        else:
            u.username = from_user.username
            u.first_name = from_user.first_name
        await session.commit()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if await _check_ban(message.from_user.id):
        await message.answer("<blockquote>⛔ Ваша учетная запись заблокирована администрацией!</blockquote>")
        return
    await _upsert_user(message.from_user)
    text = (
        f"<b>👋 Добро пожаловать, {message.from_user.first_name}!</b>\n"
        f"{SEP}\n"
        "Это <b>турнирная экосистема</b> в Telegram.\n"
        "Выбери раздел ниже, чтобы начать:\n\n"
        "<blockquote>🎯 Участвуй в турнирах, зарабатывай победы и следи за статистикой!</blockquote>"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await _help(message)


@router.callback_query(F.data == "help")
async def cb_help(cb: CallbackQuery):
    await cb.message.edit_text(
        _help_text(), reply_markup=None)
    await cb.answer()


def _help_text() -> str:
    return (
        "<b>ℹ️ ПОМОЩЬ И ПРАВИЛА</b>\n"
        f"{SEP}\n"
        "<b>🃏 Покер (Техасский Холдем):</b>\n"
        "▫️ Каждому игроку раздаётся 2 карты.\n"
        "▫️ На столе — 5 общих карт (флоп/тёрн/ривер).\n"
        "▫️ Собирается лучшая комбинация из 7 карт.\n"
        "▫️ Блайнды растут каждые N минут.\n"
        "▫️ Побеждает тот, у кого в итоге все фишки.\n\n"
        "<b>🎡 Колесо Фортуны (на выбывание):</b>\n"
        "▫️ На секторах колеса — имена участников.\n"
        "▫️ Крутится колесо — выпавший игрок выбывает.\n"
        "▫️ Последний оставшийся — победитель 🏆.\n\n"
        "<blockquote>🎯 Управление: /start — главное меню.\n"
        "Владелец: /owner. Админ: /admin.</blockquote>"
    )


async def _help(message: Message):
    await message.answer(_help_text())


@router.message(Command("owner"))
async def cmd_owner(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("<blockquote>⛔ Доступ только для владельца бота.</blockquote>")
        return
    await message.answer(
        f"<b>👑 ПАНЕЛЬ ВЛАДЕЛЬЦА</b>\n{SEP}\n"
        "Управление администраторами и блокировками:",
        reply_markup=owner_menu_kb())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with SessionLocal() as session:
        is_admin = await session.get(Admin, message.from_user.id)  # not pk; use query
    is_admin = False
    async with SessionLocal() as session:
        from sqlalchemy import select
        r = await session.execute(select(Admin).where(Admin.user_id == message.from_user.id))
        if r.scalar_one_or_none():
            is_admin = True
    if message.from_user.id != OWNER_ID and not is_admin:
        await message.answer("<blockquote>⛔ Доступ только для администраторов.</blockquote>")
        return
    await message.answer(
        f"<b>🛠 ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n{SEP}\n"
        "Здесь можно создавать и управлять турнирами:",
        reply_markup=admin_menu_kb())