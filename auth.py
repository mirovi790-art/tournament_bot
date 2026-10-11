import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from config import BOT_TOKEN


def validate_init_data(init_data: str) -> dict | None:
    if not init_data or not BOT_TOKEN:
        return None
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received_hash):
            return None
        user_json = parsed.get("user")
        if user_json:
            parsed["user_obj"] = json.loads(user_json)
        return parsed
    except Exception:
        return None