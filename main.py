import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, HOST, PORT
from database import init_db
from bot.handlers import start as h_start, owner as h_owner, admin as h_admin, \
    player as h_player, callbacks as h_callbacks
from webapp.api import create_app

logging.basicConfig(level=logging.INFO)


async def poker_ticker():
    """Автоматический таймаут хода в покере + автопереход к новой раздаче."""
    from game import manager as gm
    while True:
        try:
            for tid, g in list(gm._active_poker.items()):
                if g.finished:
                    continue
                changed = False
                if g.check_timeout():
                    changed = True
                # auto-start next hand when showdown after 4 seconds
                if g.phase == "showdown" and hasattr(g, "_showdown_at"):
                    if asyncio.get_event_loop().time() - g._showdown_at > 4:
                        g.start_hand()
                        changed = True
                elif g.phase == "showdown":
                    g._showdown_at = asyncio.get_event_loop().time()
                if changed:
                    await gm.broadcast(tid, g.to_dict())
        except Exception as e:
            logging.exception("ticker error: %s", e)
        await asyncio.sleep(1)


async def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN не задан в .env")

    await init_db()

    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(h_start.router)
    dp.include_router(h_owner.router)
    dp.include_router(h_admin.router)
    dp.include_router(h_player.router)
    dp.include_router(h_callbacks.router)

    app = create_app(bot)
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info", loop="asyncio")
    server = uvicorn.Server(config)

    logging.info("🚀 Бот и Mini App сервер запущены на %s:%s", HOST, PORT)

    await asyncio.gather(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        server.serve(),
        poker_ticker(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Остановлено")