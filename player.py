from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database import SessionLocal
from models import Tournament, Participant, User
from keyboards import apply_kb, enter_webapp_kb, back_kb, main_menu_kb
from config import WEBAPP_URL
from utils import SEP, esc

router = Router()


@router.callback_query(F.data == "open_tournaments")
async def cb_open(cb: CallbackQuery):
    async with SessionLocal() as session:
        r = await session.execute(
            select(Tournament).where(Tournament.access_type == "open",
                                    Tournament.status == "registration"))
        tours = r.scalars().all()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if not tours:
        await cb.message.edit_text(
            f"<b>🏆 Открытые турниры</b>\n{SEP}\n"
            "<blockquote>Пока нет открытых турниров на регистрации.</blockquote>",
            reply_markup=back_kb("back_main"))
        await cb.answer(); return
    lines = [f"<b>🏆 Открытые турниры</b>\n{SEP}"]
    rows = []
    for t in tours:
        emoji = "🃏" if t.game_type == "poker" else "🎡"
        lines.append(f"{emoji} <b>{esc(t.name)}</b> · ID <code>{t.id}</code>")
        rows.append([InlineKeyboardButton(
            text=f"📩 Подать заявку · {t.name[:20]}",
            callback_data=f"apply_{t.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    await cb.message.edit_text("\n".join(lines),
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("apply_"))
async def cb_apply(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if not t:
            await cb.answer("Турнир не найден", show_alert=True); return
        r = await session.execute(select(Participant).where(
            Participant.tournament_id == tid, Participant.user_id == cb.from_user.id))
        existing = r.scalar_one_or_none()
        if existing and existing.status in ("pending", "approved"):
            await cb.answer("Заявка уже подана", show_alert=True); return
        if existing:
            existing.status = "pending"
            pid = existing.id
        else:
            p = Participant(tournament_id=tid, user_id=cb.from_user.id, status="pending")
            session.add(p)
            await session.commit()
            await session.refresh(p)
            pid = p.id
        creator_id = t.creator_id
        tname = t.name
    # notify creator
    try:
        await cb.bot.send_message(
            creator_id,
            f"<b>📩 Новая заявка на турнир!</b>\n{SEP}\n"
            f"👤 Игрок: @{cb.from_user.username or cb.from_user.first_name} "
            f"(ID: <code>{cb.from_user.id}</code>)\n"
            f"🏆 Турнир: <b>{esc(tname)}</b>",
            reply_markup=__import__("keyboards").join_request_kb(pid))
    except Exception:
        pass
    await cb.answer("Заявка отправлена!", show_alert=True)


@router.callback_query(F.data == "my_tournaments")
async def cb_my(cb: CallbackQuery):
    async with SessionLocal() as session:
        r = await session.execute(select(Participant).where(
            Participant.user_id == cb.from_user.id,
            Participant.status.in_(("approved", "winner"))))
        parts = r.scalars().all()
        rows = []
        lines = [f"<b>🎟 Мои турниры</b>\n{SEP}"]
        for p in parts:
            t = await session.get(Tournament, p.tournament_id)
            if not t:
                continue
            emoji = "🃏" if t.game_type == "poker" else "🎡"
            lines.append(f"{emoji} <b>{esc(t.name)}</b> · <code>{t.status}</code>")
            if t.status in ("running", "paused"):
                rows.append([__import__("aiogram.types").types.InlineKeyboardButton(
                    text=f"🎮 Войти: {t.name[:20]}",
                    web_app=__import__("aiogram.types").types.WebAppInfo(
                        url=f"{WEBAPP_URL}/?tid={t.id}"))])
        if not parts:
            lines.append("<blockquote>ℹ️ Пока нет активных турниров.</blockquote>")
        rows.append([__import__("aiogram.types").types.InlineKeyboardButton(
            text="⬅️ Назад", callback_data="back_main")])
        await cb.message.edit_text(
            "\n".join(lines),
            reply_markup=__import__("aiogram.types").types.InlineKeyboardMarkup(
                inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data == "profile")
async def cb_profile(cb: CallbackQuery):
    async with SessionLocal() as session:
        u = await session.get(User, cb.from_user.id)
        if u is None:
            u = User(id=cb.from_user.id, username=cb.from_user.username,
                     first_name=cb.from_user.first_name)
            session.add(u)
            await session.commit()
        r = await session.execute(select(Participant).where(
            Participant.user_id == cb.from_user.id,
            Participant.status == "winner"))
        wins = len(r.scalars().all())
    text = (
        f"<b>👤 ПРОФИЛЬ ИГРОКА</b>\n"
        f"{SEP}\n"
        f"🆔 Telegram ID: <code>{cb.from_user.id}</code>\n"
        f"👤 Имя: {esc(cb.from_user.first_name)}\n"
        f"🌐 Username: @{cb.from_user.username or '—'}\n"
        f"💰 Баланс фишек: <code>{u.chips}</code>\n"
        f"🏆 Побед: <code>{wins}</code>"
    )
    await cb.message.edit_text(text, reply_markup=back_kb("back_main"))
    await cb.answer()


@router.callback_query(F.data == "back_main")
async def cb_back_main(cb: CallbackQuery):
    text = (
        f"<b>🏠 Главное меню</b>\n{SEP}\n"
        "Выбери раздел:"
    )
    await cb.message.edit_text(text, reply_markup=main_menu_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("accept_invite_"))
async def cb_accept_invite(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        r = await session.execute(select(Participant).where(
            Participant.tournament_id == tid, Participant.user_id == cb.from_user.id))
        p = r.scalar_one_or_none()
        t = await session.get(Tournament, tid)
        if not p or not t:
            await cb.answer("Не найдено", show_alert=True); return
        p.status = "approved"
        await session.commit()
    await cb.message.edit_text(
        f"<b>✅ Вы приняли приглашение!</b>\n{SEP}\n"
        f"🏆 <code>{esc(t.name)}</code>\n\n"
        "<blockquote>Ожидайте старта турнира от администратора.</blockquote>")
    await cb.answer("Принято")


@router.callback_query(F.data.startswith("decline_invite_"))
async def cb_decline_invite(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        r = await session.execute(select(Participant).where(
            Participant.tournament_id == tid, Participant.user_id == cb.from_user.id))
        p = r.scalar_one_or_none()
        if p:
            p.status = "rejected"
            await session.commit()
    await cb.message.edit_text("<blockquote>❌ Вы отклонили приглашение.</blockquote>")
    await cb.answer()