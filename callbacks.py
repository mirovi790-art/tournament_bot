from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from database import SessionLocal
from models import Participant, Tournament, User
from keyboards import enter_webapp_kb
from config import WEBAPP_URL
from utils import SEP, esc

router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def cb_approve(cb: CallbackQuery):
    pid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        p = await session.get(Participant, pid)
        if not p:
            await cb.answer("Заявка не найдена", show_alert=True); return
        p.status = "approved"
        t = await session.get(Tournament, p.tournament_id)
        await session.commit()
        tname = t.name if t else "?"
        uid = p.user_id
    try:
        await cb.bot.send_message(
            uid,
            f"<b>✅ Ваша заявка одобрена!</b>\n{SEP}\n"
            f"🏆 <code>{esc(tname)}</code>\n\n"
            "<blockquote>Ожидайте старта турнира.</blockquote>")
    except Exception:
        pass
    await cb.message.edit_text(
        f"<b>✅ Игрок принят</b>\n{SEP}\nID заявки: <code>{pid}</code>")
    await cb.answer("Принято")


@router.callback_query(F.data.startswith("reject_"))
async def cb_reject(cb: CallbackQuery):
    pid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        p = await session.get(Participant, pid)
        if not p:
            await cb.answer("Заявка не найдена", show_alert=True); return
        p.status = "rejected"
        t = await session.get(Tournament, p.tournament_id)
        await session.commit()
        tname = t.name if t else "?"
        uid = p.user_id
    try:
        await cb.bot.send_message(
            uid,
            f"<b>❌ Заявка отклонена</b>\n{SEP}\n🏆 <code>{esc(tname)}</code>")
    except Exception:
        pass
    await cb.message.edit_text(
        f"<b>❌ Игрок отклонён</b>\n{SEP}\nID заявки: <code>{pid}</code>")
    await cb.answer("Отклонено")