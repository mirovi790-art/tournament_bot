from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import OWNER_ID, WEBAPP_URL
from database import SessionLocal
from models import Admin, Tournament, Participant, User, Ban
from game.manager import set_poker, set_wheel, get_poker, get_wheel, broadcast
from game.poker import PokerGame
from game.wheel import WheelGame
from keyboards import (admin_menu_kb, access_type_kb, game_type_kb, confirm_kb,
                       back_kb, manage_tournament_kb, invite_response_kb)
from utils import SEP, esc

router = Router()


class TournamentFSM(StatesGroup):
    access_type = State()
    game_type = State()
    name = State()
    poker_stack = State()
    poker_turn = State()
    poker_blind = State()
    wheel_prize = State()
    confirm = State()


class InviteFSM(StatesGroup):
    user_id = State()


async def _is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    async with SessionLocal() as session:
        r = await session.execute(select(Admin).where(Admin.user_id == user_id))
        return r.scalar_one_or_none() is not None


@router.callback_query(F.data == "admin_create_tournament")
async def cb_create(cb: CallbackQuery, state: FSMContext):
    if not await _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    await state.clear()
    await state.set_state(TournamentFSM.access_type)
    await cb.message.edit_text(
        f"<b>🆕 Создание турнира · Шаг 1/5</b>\n{SEP}\n"
        "Выбери <b>формат доступа</b>:",
        reply_markup=access_type_kb())
    await cb.answer()


@router.callback_query(F.data == "tt_access_open")
async def tt_access_open(cb: CallbackQuery, state: FSMContext):
    await state.update_data(access_type="open")
    await state.set_state(TournamentFSM.game_type)
    await cb.message.edit_text(
        f"<b>🆕 Создание турнира · Шаг 2/5</b>\n{SEP}\n"
        "Выбери <b>тип игры</b>:",
        reply_markup=game_type_kb())
    await cb.answer()


@router.callback_query(F.data == "tt_access_closed")
async def tt_access_closed(cb: CallbackQuery, state: FSMContext):
    await state.update_data(access_type="closed")
    await state.set_state(TournamentFSM.game_type)
    await cb.message.edit_text(
        f"<b>🆕 Создание турнира · Шаг 2/5</b>\n{SEP}\n"
        "Выбери <b>тип игры</b>:",
        reply_markup=game_type_kb())
    await cb.answer()


@router.callback_query(F.data == "tt_game_poker")
async def tt_game_poker(cb: CallbackQuery, state: FSMContext):
    await state.update_data(game_type="poker")
    await state.set_state(TournamentFSM.name)
    await cb.message.edit_text(
        f"<b>🆕 Создание турнира · Шаг 3/5</b>\n{SEP}\n"
        "Введи <b>название турнира</b>:")
    await cb.answer()


@router.callback_query(F.data == "tt_game_wheel")
async def tt_game_wheel(cb: CallbackQuery, state: FSMContext):
    await state.update_data(game_type="wheel")
    await state.set_state(TournamentFSM.name)
    await cb.message.edit_text(
        f"<b>🆕 Создание турнира · Шаг 3/5</b>\n{SEP}\n"
        "Введи <b>название турнира</b>:")
    await cb.answer()


@router.message(TournamentFSM.name)
async def tt_name(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    name = message.text.strip()[:100]
    await state.update_data(name=name)
    data = await state.get_data()
    if data["game_type"] == "poker":
        await state.set_state(TournamentFSM.poker_stack)
        await message.answer(
            f"<b>🆕 Шаг 4/5 · Покер</b>\n{SEP}\n"
            "Введи <b>стартовый стек фишек</b> (например, 1000):")
    else:
        await state.set_state(TournamentFSM.wheel_prize)
        await message.answer(
            f"<b>🆕 Шаг 4/5 · Колесо</b>\n{SEP}\n"
            "Введи <b>описание приза</b>:")
    await state.update_data(name=name)


@router.message(TournamentFSM.poker_stack)
async def tt_stack(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    try:
        stack = int(message.text.strip())
        assert 10 <= stack <= 1_000_000
    except Exception:
        await message.answer("<blockquote>❌ Введи целое число от 10 до 1 000 000.</blockquote>")
        return
    await state.update_data(poker_stack=stack)
    await state.set_state(TournamentFSM.poker_turn)
    await message.answer(
        f"<b>🆕 Шаг 4/5 · Покер</b>\n{SEP}\n"
        "Введи <b>время на ход в секундах</b> (например, 20):")


@router.message(TournamentFSM.poker_turn)
async def tt_turn(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    try:
        t = int(message.text.strip())
        assert 5 <= t <= 300
    except Exception:
        await message.answer("<blockquote>❌ Введи целое число от 5 до 300.</blockquote>")
        return
    await state.update_data(poker_turn=t)
    await state.set_state(TournamentFSM.poker_blind)
    await message.answer(
        f"<b>🆕 Шаг 5/5 · Покер</b>\n{SEP}\n"
        "Введи <b>интервал роста блайндов в минутах</b> (например, 5):")


@router.message(TournamentFSM.poker_blind)
async def tt_blind(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    try:
        b = int(message.text.strip())
        assert 1 <= b <= 120
    except Exception:
        await message.answer("<blockquote>❌ Введи целое число от 1 до 120.</blockquote>")
        return
    await state.update_data(poker_blind=b)
    await _show_confirm(message, state)


@router.message(TournamentFSM.wheel_prize)
async def tt_prize(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    prize = message.text.strip()[:200]
    await state.update_data(prize=prize)
    await _show_confirm(message, state)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(TournamentFSM.confirm)
    lines = [
        "<b>✅ ПОДТВЕРЖДЕНИЕ СОЗДАНИЯ</b>",
        SEP,
        f"<b>🏆 Название:</b> <code>{esc(data['name'])}</code>",
        f"<b>Тип доступа:</b> {'🟢 Открытый' if data['access_type']=='open' else '🔴 Закрытый'}",
        f"<b>Тип игры:</b> {'🃏 Покер' if data['game_type']=='poker' else '🎡 Колесо Фортуны'}",
    ]
    if data["game_type"] == "poker":
        lines += [
            f"🔹 Стартовый стек: <code>{data['poker_stack']}</code>",
            f"🔹 Тайм-банк: <code>{data['poker_turn']} сек</code>",
            f"🔹 Рост блайндов: каждые <code>{data['poker_blind']} мин</code>",
        ]
    else:
        lines += [f"🔹 Приз: <i>{esc(data['prize'])}</i>"]
    lines.append("\n<blockquote>Нажми ✅ для создания.</blockquote>")
    await message.answer("\n".join(lines), reply_markup=confirm_kb())


@router.callback_query(F.data == "tt_confirm")
async def tt_confirm(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with SessionLocal() as session:
        t = Tournament(
            name=data["name"],
            access_type=data["access_type"],
            game_type=data["game_type"],
            creator_id=cb.from_user.id,
            start_stack=data.get("poker_stack", 1000),
            turn_time=data.get("poker_turn", 20),
            blind_interval=data.get("poker_blind", 5),
            prize=data.get("prize"),
        )
        session.add(t)
        await session.commit()
        await session.refresh(t)
    await state.clear()
    await cb.message.edit_text(
        f"<b>🎉 Турнир создан!</b>\n{SEP}\n"
        f"🏆 <code>{esc(t.name)}</code>\n"
        f"🆔 Турнир ID: <code>{t.id}</code>\n\n"
        "<blockquote>Открой /admin → 📂 Управление турнирами для запуска.</blockquote>",
        reply_markup=back_kb("admin_back"))
    await cb.answer("Готово!")


@router.callback_query(F.data == "admin_cancel_fsm")
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        f"<b>🛠 ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n{SEP}",
        reply_markup=admin_menu_kb())
    await cb.answer("Отменено")


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        f"<b>🛠 ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n{SEP}",
        reply_markup=admin_menu_kb())
    await cb.answer()


@router.callback_query(F.data == "admin_manage_tournaments")
async def cb_manage(cb: CallbackQuery):
    if not await _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    async with SessionLocal() as session:
        r = await session.execute(select(Tournament).order_by(Tournament.id.desc()).limit(20))
        tours = r.scalars().all()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for t in tours:
        emoji = "🃏" if t.game_type == "poker" else "🎡"
        lock = "🟢" if t.access_type == "open" else "🔴"
        rows.append([InlineKeyboardButton(
            text=f"{emoji}{lock} {t.name} · {t.status}",
            callback_data=f"tt_manage_{t.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    await cb.message.edit_text(
        f"<b>📂 Управление турнирами</b>\n{SEP}\nВыбери турнир:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()


@router.callback_query(F.data.startswith("tt_manage_"))
async def cb_manage_one(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if not t:
            await cb.answer("Турнир не найден", show_alert=True); return
        r = await session.execute(
            select(Participant).where(Participant.tournament_id == tid))
        parts = r.scalars().all()
    approved = [p for p in parts if p.status in ("approved", "winner")]
    text = (
        f"<b>🏆 ТУРНИР:</b> <code>{esc(t.name)}</code>\n"
        f"{SEP}\n"
        f"<b>ID:</b> <code>{t.id}</code>\n"
        f"<b>Тип игры:</b> {'🃏 Покер' if t.game_type=='poker' else '🎡 Колесо'}\n"
        f"<b>Формат:</b> {'🟢 Открытый' if t.access_type=='open' else '🔴 Закрытый'}\n"
        f"<b>Статус:</b> <code>{t.status}</code>\n"
        f"<b>Участников:</b> <code>{len(approved)}</code>\n"
    )
    await cb.message.edit_text(text, reply_markup=manage_tournament_kb(t.id, t.status))
    await cb.answer()


@router.callback_query(F.data.startswith("tt_start_"))
async def cb_start(cb: CallbackQuery):
    if not await _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if not t:
            await cb.answer("Нет турнира", show_alert=True); return
        r = await session.execute(
            select(Participant).where(Participant.tournament_id == tid,
                                      Participant.status == "approved"))
        parts = r.scalars().all()
        if len(parts) < 2:
            await cb.answer("Нужно минимум 2 участника", show_alert=True); return
        # gather user names
        players = []
        for p in parts:
            u = await session.get(User, p.user_id)
            players.append({
                "user_id": p.user_id,
                "name": (u.first_name if u and u.first_name else str(p.user_id)),
            })
            p.chips = t.start_stack
        t.status = "running"
        await session.commit()

    if t.game_type == "poker":
        g = PokerGame(tid, players, start_stack=t.start_stack,
                      turn_time=t.turn_time, blind_interval=t.blind_interval)
        set_poker(tid, g)
        g.next_blind_at = g.turn_deadline
        g.start_hand()
        await broadcast(tid, g.to_dict())
    else:
        g = WheelGame(tid, players, t.prize or "🏆 Приз")
        set_wheel(tid, g)
        await broadcast(tid, g.to_dict())

    # notify participants
    from keyboards import enter_webapp_kb
    for p in parts:
        try:
            await cb.bot.send_message(
                p.user_id,
                f"<b>🚀 Турнир запущен!</b>\n{SEP}\n"
                f"🏆 <code>{esc(t.name)}</code>\n\n"
                "<blockquote>Нажми кнопку, чтобы войти в игру.</blockquote>",
                reply_markup=enter_webapp_kb(tid, WEBAPP_URL))
        except Exception:
            pass
    await cb.answer("Запущено!")
    await cb_manage_one(cb)


@router.callback_query(F.data.startswith("tt_pause_"))
async def cb_pause(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if t:
            t.status = "paused"
            await session.commit()
    await cb.answer("Пауза")
    await cb_manage_one(cb)


@router.callback_query(F.data.startswith("tt_resume_"))
async def cb_resume(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if t:
            t.status = "running"
            await session.commit()
    await cb.answer("Продолжено")
    await cb_manage_one(cb)


@router.callback_query(F.data.startswith("tt_cancel_"))
async def cb_cancel_tour(cb: CallbackQuery):
    tid = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if t:
            t.status = "cancelled"
            await session.commit()
    await broadcast(tid, {"type": "tournament_cancelled", "tid": tid})
    await cb.answer("Отменён")
    await cb_manage_one(cb)


@router.callback_query(F.data.startswith("tt_invite_"))
async def cb_invite(cb: CallbackQuery, state: FSMContext):
    if not await _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    tid = int(cb.data.split("_")[-1])
    await state.update_data(invite_tid=tid)
    await state.set_state(InviteFSM.user_id)
    await cb.message.edit_text(
        f"<b>✉️ Приглашение игрока</b>\n{SEP}\n"
        "Отправь <b>Telegram User ID</b> игрока:",
        reply_markup=back_kb(f"tt_manage_{tid}"))
    await cb.answer()


@router.message(InviteFSM.user_id)
async def msg_invite(message: Message, state: FSMContext):
    if not await _is_admin(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("<blockquote>❌ Нужен числовой ID.</blockquote>")
        return
    data = await state.get_data()
    tid = data.get("invite_tid")
    async with SessionLocal() as session:
        t = await session.get(Tournament, tid)
        if not t:
            await message.answer("<blockquote>❌ Турнир не найден.</blockquote>")
            await state.clear(); return
        r = await session.execute(select(Participant).where(
            Participant.tournament_id == tid, Participant.user_id == uid))
        existing = r.scalar_one_or_none()
        if existing:
            existing.status = "approved"
        else:
            session.add(Participant(tournament_id=tid, user_id=uid, status="approved"))
        await session.commit()
        tname = t.name
    await state.clear()
    try:
        await message.bot.send_message(
            uid,
            f"<b>✉️ Вас пригласили в турнир!</b>\n{SEP}\n"
            f"🏆 <code>{esc(tname)}</code>\n\n"
            "<blockquote>Примешь приглашение?</blockquote>",
            reply_markup=invite_response_kb(tid))
        await message.answer(
            f"<b>✅ Приглашение отправлено</b>\n{SEP}\n🆔 <code>{uid}</code>")
    except Exception as e:
        await message.answer(f"<blockquote>⚠️ Не удалось отправить: {esc(str(e))}</blockquote>")


@router.callback_query(F.data.startswith("tt_kick_"))
async def cb_kick(cb: CallbackQuery, state: FSMContext):
    if not await _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True); return
    tid = int(cb.data.split("_")[-1])
    await state.update_data(kick_tid=tid)
    await state.set_state(InviteFSM.user_id)
    # reuse state but flag as kick
    await state.update_data(invite_tid=tid, is_kick=True)
    await cb.message.edit_text(
        f"<b>🚫 Кик игрока</b>\n{SEP}\nОтправь Telegram ID игрока:",
        reply_markup=back_kb(f"tt_manage_{tid}"))
    await cb.answer()