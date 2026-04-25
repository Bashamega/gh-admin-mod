from gh_admin_mod.env import get_env


def set_output(name: str, value: str) -> None:
    output_path = get_env("GITHUB_OUTPUT")
    if not output_path:
        return

    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")
