import os


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def parse_upper_set(value: str) -> set[str]:
    return {item.upper() for item in parse_csv(value)}


def normalize_user(value: str) -> str:
    return value.strip().lstrip("@").lower()
