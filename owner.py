from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from config import OWNER_ID
from database import SessionLocal
from models import Admin, Ban, User
from keyboards import owner_menu_kb, back_kb
from utils import SEP

router = Router()


class OwnerForm(StatesGroup):
    add_admin = State()
    ban_id = State()
    unban_id = State()


def _is_owner(uid: int) -> bool:
    return uid == OWNER_ID


@router.callback_query(F.data == "owner_add_admin")
async def cb_add_admin(cb: CallbackQuery, state: FSMContext):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    await state.set_state(OwnerForm.add_admin)
    await cb.message.edit_text(
        "<b>➕ Добавить администратора</b>\n"
        f"{SEP}\n"
        "Отправь <b>Telegram ID</b> или <b>@username</b> пользователя.\n\n"
        "<blockquote>⚠️ Пользователь должен был хотя бы раз запустить бота (/start).</blockquote>",
        reply_markup=back_kb("owner_back"))
    await cb.answer()


@router.message(OwnerForm.add_admin)
async def msg_add_admin(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    raw = message.text.strip()
    target_id = None
    async with SessionLocal() as session:
        if raw.startswith("@"):
            r = await session.execute(select(User).where(User.username == raw[1:]))
            u = r.scalar_one_or_none()
            if u:
                target_id = u.id
        else:
            try:
                target_id = int(raw)
            except ValueError:
                target_id = None
        if target_id is None:
            await message.answer("<blockquote>❌ Пользователь не найден. Убедись, что он запускал /start.</blockquote>")
            return
        existing = await session.execute(select(Admin).where(Admin.user_id == target_id))
        if existing.scalar_one_or_none():
            await message.answer("<blockquote>ℹ️ Этот пользователь уже администратор.</blockquote>")
            return
        session.add(Admin(user_id=target_id))
        await session.commit()
    await state.clear()
    await message.answer(
        f"<b>✅ Администратор добавлен</b>\n{SEP}\n"
        f"🆔 <code>{target_id}</code>", reply_markup=owner_menu_kb())


@router.callback_query(F.data == "owner_del_admin")
async def cb_del_admin(cb: CallbackQuery):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    async with SessionLocal() as session:
        r = await session.execute(select(Admin))
        admins = r.scalars().all()
    if not admins:
        await cb.message.edit_text(
            "<blockquote>ℹ️ Администраторов нет.</blockquote>",
            reply_markup=back_kb("owner_back"))
        await cb.answer(); return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = [[InlineKeyboardButton(text=f"❌ {a.user_id}", callback_data=f"owner_rm_{a.user_id}")]
            for a in admins]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="owner_back")])
    await cb.message.edit_text(
        f"<b>➖ Удалить администратора</b>\n{SEP}\nВыбери кого удалить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("owner_rm_"))
async def cb_rm_admin(cb: CallbackQuery):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    uid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        r = await session.execute(select(Admin).where(Admin.user_id == uid))
        a = r.scalar_one_or_none()
        if a:
            await session.delete(a)
            await session.commit()
    await cb.answer("Удалён")
    await cb_del_admin(cb)


@router.callback_query(F.data == "owner_list_admins")
async def cb_list_admins(cb: CallbackQuery):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    async with SessionLocal() as session:
        r = await session.execute(select(Admin))
        admins = r.scalars().all()
    if not admins:
        text = f"<b>📋 Список администраторов</b>\n{SEP}\n<blockquote>ℹ️ Пока никого.</blockquote>"
    else:
        lines = [f"<b>📋 Список администраторов</b>\n{SEP}"]
        for i, a in enumerate(admins, 1):
            lines.append(f"🔹 <code>{a.user_id}</code> · с {a.added_at:%d.%m.%Y}")
        text = "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=back_kb("owner_back"))
    await cb.answer()


@router.callback_query(F.data == "owner_ban")
async def cb_ban(cb: CallbackQuery, state: FSMContext):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    await state.set_state(OwnerForm.ban_id)
    await cb.message.edit_text(
        f"<b>🚫 Забанить игрока</b>\n{SEP}\nОтправь Telegram ID игрока:",
        reply_markup=back_kb("owner_back"))
    await cb.answer()


@router.message(OwnerForm.ban_id)
async def msg_ban(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("<blockquote>❌ Нужен числовой Telegram ID.</blockquote>")
        return
    async with SessionLocal() as session:
        if await session.get(Ban, uid) is None:
            session.add(Ban(user_id=uid))
            await session.commit()
    await state.clear()
    try:
        await message.bot.send_message(
            uid, "<blockquote>⛔ Ваша учетная запись заблокирована администрацией!</blockquote>")
    except Exception:
        pass
    await message.answer(
        f"<b>✅ Игрок забанен</b>\n{SEP}\n🆔 <code>{uid}</code>",
        reply_markup=owner_menu_kb())


@router.callback_query(F.data == "owner_unban")
async def cb_unban(cb: CallbackQuery, state: FSMContext):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    await state.set_state(OwnerForm.unban_id)
    await cb.message.edit_text(
        f"<b>✅ Разбанить игрока</b>\n{SEP}\nОтправь Telegram ID:",
        reply_markup=back_kb("owner_back"))
    await cb.answer()


@router.message(OwnerForm.unban_id)
async def msg_unban(message: Message, state: FSMContext):
    if not _is_owner(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("<blockquote>❌ Нужен числовой Telegram ID.</blockquote>")
        return
    async with SessionLocal() as session:
        b = await session.get(Ban, uid)
        if b:
            await session.delete(b)
            await session.commit()
    await state.clear()
    await message.answer(
        f"<b>✅ Игрок разбанен</b>\n{SEP}\n🆔 <code>{uid}</code>",
        reply_markup=owner_menu_kb())


@router.callback_query(F.data == "owner_blacklist")
async def cb_blacklist(cb: CallbackQuery):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    async with SessionLocal() as session:
        r = await session.execute(select(Ban))
        bans = r.scalars().all()
    if not bans:
        text = f"<b>📜 Черный список</b>\n{SEP}\n<blockquote>✅ Пусто.</blockquote>"
    else:
        lines = [f"<b>📜 Черный список</b>\n{SEP}"]
        for b in bans:
            lines.append(f"🚫 <code>{b.user_id}</code> · {b.banned_at:%d.%m.%Y}")
        text = "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=back_kb("owner_back"))
    await cb.answer()


@router.callback_query(F.data == "owner_back")
async def cb_owner_back(cb: CallbackQuery, state: FSMContext):
    if not _is_owner(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    await state.clear()
    await cb.message.edit_text(
        f"<b>👑 ПАНЕЛЬ ВЛАДЕЛЬЦА</b>\n{SEP}\nУправление администраторами и блокировками:",
        reply_markup=owner_menu_kb())
    await cb.answer()