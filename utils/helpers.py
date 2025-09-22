from typing import Any, Dict
import json


def sanitize_user_input(text: str) -> str:
    if not text:
        return ""
    return text.strip()[:1000]


def format_user_data(user_data: Dict[str, Any]) -> str:
    return json.dumps(user_data, ensure_ascii=False, indent=2)


def extract_referral_code(start_param: str) -> str:
    if start_param and start_param.startswith("friend_"):
        return start_param[7:]
    return ""


def validate_time_format(time_str: str) -> bool:
    import re
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))
