import asyncio
from game.poker import PokerGame
from game.wheel import WheelGame

_active_poker: dict[int, PokerGame] = {}
_active_wheel: dict[int, WheelGame] = {}
_connections: dict[int, set] = {}
_lock = asyncio.Lock()


def get_poker(tid: int) -> PokerGame | None:
    return _active_poker.get(tid)


def get_wheel(tid: int) -> WheelGame | None:
    return _active_wheel.get(tid)


def set_poker(tid: int, g: PokerGame):
    _active_poker[tid] = g


def set_wheel(tid: int, g: WheelGame):
    _active_wheel[tid] = g


def remove_tournament(tid: int):
    _active_poker.pop(tid, None)
    _active_wheel.pop(tid, None)


def connect(tid: int, ws):
    _connections.setdefault(tid, set()).add(ws)


def disconnect(tid: int, ws):
    s = _connections.get(tid)
    if s and ws in s:
        s.discard(ws)


async def broadcast(tid: int, message: dict):
    if tid not in _connections:
        return
    dead = []
    for ws in list(_connections[tid]):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for w in dead:
        disconnect(tid, w)