def notice(message: str) -> None:
    print(f"::notice::{message}")


def error(message: str) -> None:
    print(f"::error::{message}")


def fail(message: str) -> None:
    error(message)
    raise SystemExit(1)
