import json
import urllib.error
import urllib.request

from gh_admin_mod.env import get_env
from gh_admin_mod.logging import fail
from gh_admin_mod.models import ModerationContext


def api_request(method: str, url: str, payload: dict | None = None) -> dict | None:
    token = get_env("GITHUB_TOKEN")
    if not token:
        fail("GITHUB_TOKEN is not available.")

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "gh-admin-mod",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8").strip()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"GitHub API request failed ({exc.code}) for {url}: {body}")


def _base_api(context: ModerationContext) -> str:
    return f"https://api.github.com/repos/{context.owner}/{context.repo}"


def create_comment(context: ModerationContext, body: str) -> None:
    api_request(
        "POST",
        f"{_base_api(context)}/issues/{context.issue_number}/comments",
        {"body": body},
    )


def add_labels(context: ModerationContext, labels: list[str]) -> None:
    if not labels:
        return

    api_request(
        "POST",
        f"{_base_api(context)}/issues/{context.issue_number}/labels",
        {"labels": labels},
    )


def close_item(context: ModerationContext, close_reason: str) -> None:
    if context.is_pull_request:
        api_request(
            "PATCH",
            f"{_base_api(context)}/pulls/{context.issue_number}",
            {"state": "closed"},
        )
        return

    api_request(
        "PATCH",
        f"{_base_api(context)}/issues/{context.issue_number}",
        {"state": "closed", "state_reason": close_reason},
    )


def lock_item(context: ModerationContext) -> None:
    api_request(
        "PUT",
        f"{_base_api(context)}/issues/{context.issue_number}/lock",
        {"lock_reason": "resolved"},
    )
