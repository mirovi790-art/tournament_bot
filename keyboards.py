from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Открытые турниры", callback_data="open_tournaments")],
        [InlineKeyboardButton(text="🎟 Мои турниры", callback_data="my_tournaments")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])


def owner_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="owner_add_admin")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="owner_del_admin")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="owner_list_admins")],
        [InlineKeyboardButton(text="🚫 Забанить игрока", callback_data="owner_ban")],
        [InlineKeyboardButton(text="✅ Разбанить игрока", callback_data="owner_unban")],
        [InlineKeyboardButton(text="📜 Черный список", callback_data="owner_blacklist")],
    ])


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать турнир", callback_data="admin_create_tournament")],
        [InlineKeyboardButton(text="📂 Управление турнирами", callback_data="admin_manage_tournaments")],
    ])


def back_kb(target: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=target)]
    ])


def access_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Открытый", callback_data="tt_access_open")],
        [InlineKeyboardButton(text="🔴 Закрытый", callback_data="tt_access_closed")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_fsm")],
    ])


def game_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Покер", callback_data="tt_game_poker")],
        [InlineKeyboardButton(text="🎡 Колесо Фортуны", callback_data="tt_game_wheel")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_fsm")],
    ])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать", callback_data="tt_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_fsm")],
    ])


def apply_kb(tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Подать заявку", callback_data=f"apply_{tid}")]
    ])


def enter_webapp_kb(tid: int, url: str) -> InlineKeyboardMarkup:
    from aiogram.types import WebAppInfo
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Войти в турнир (Mini App)",
                              web_app=WebAppInfo(url=f"{url}/?tid={tid}"))]
    ])


def join_request_kb(pid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{pid}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{pid}")]
    ])


def invite_response_kb(tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_invite_{tid}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_invite_{tid}")]
    ])


def manage_tournament_kb(tid: int, status: str) -> InlineKeyboardMarkup:
    rows = []
    if status == "registration":
        rows.append([InlineKeyboardButton(text="▶️ Запустить", callback_data=f"tt_start_{tid}")])
    if status == "running":
        rows.append([InlineKeyboardButton(text="⏸ Пауза", callback_data=f"tt_pause_{tid}")])
        rows.append([InlineKeyboardButton(text="✉️ Пригласить игрока", callback_data=f"tt_invite_{tid}")])
        rows.append([InlineKeyboardButton(text="🚫 Кик игрока", callback_data=f"tt_kick_{tid}")])
        rows.append([InlineKeyboardButton(text="🛑 Отменить", callback_data=f"tt_cancel_{tid}")])
    if status == "paused":
        rows.append([InlineKeyboardButton(text="▶️ Продолжить", callback_data=f"tt_resume_{tid}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage_tournaments")])
    return InlineKeyboardMarkup(inline_keyboard=rows)