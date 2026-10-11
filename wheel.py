import random


class WheelGame:
    def __init__(self, tid, participants, prize):
        self.tid = tid
        self.prize = prize or "🏆 Приз"
        self.active = [{"user_id": p["user_id"], "name": p["name"]} for p in participants]
        self.eliminated = []  # list of {user_id, name, place}
        self.spin_count = 0
        self.finished = False
        self.winner = None
        self.last_spin = None  # {"eliminated": ..., "sector_index": ...}

    def spin(self):
        if self.finished or len(self.active) < 2:
            return None
        idx = random.randrange(len(self.active))
        eliminated = self.active.pop(idx)
        place = len(self.active) + 1
        self.eliminated.append({**eliminated, "place": place})
        self.spin_count += 1
        self.last_spin = {"eliminated": eliminated, "sector_index": idx}
        if len(self.active) == 1:
            self.winner = self.active[0]
            self.winner["place"] = 1
            self.finished = True
        return eliminated

    def to_dict(self):
        return {
            "type": "wheel_state",
            "tid": self.tid,
            "active": self.active,
            "eliminated": self.eliminated,
            "spin_count": self.spin_count,
            "finished": self.finished,
            "winner": self.winner,
            "prize": self.prize,
            "last_spin": self.last_spin,
        }