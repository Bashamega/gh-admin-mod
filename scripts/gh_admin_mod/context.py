import json

from gh_admin_mod.env import get_env
from gh_admin_mod.logging import fail
from gh_admin_mod.models import ModerationContext


def load_event() -> dict:
    event_path = get_env("GITHUB_EVENT_PATH")
    if not event_path:
        fail("GITHUB_EVENT_PATH is not available.")

    with open(event_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_context() -> ModerationContext:
    event = load_event()
    issue = event.get("issue")
    pull_request = event.get("pull_request")
    payload_item = issue or pull_request

    if not payload_item:
        fail("This action only supports issue and pull request events.")

    repository = get_env("GITHUB_REPOSITORY")
    if "/" not in repository:
        fail("GITHUB_REPOSITORY is not available.")

    owner, repo = repository.split("/", 1)
    is_pull_request = pull_request is not None

    sender_association = str(
        event.get("author_association")
        or (event.get("sender") or {}).get("author_association")
        or ""
    ).upper()

    return ModerationContext(
        owner=owner,
        repo=repo,
        issue_number=int(payload_item["number"]),
        is_pull_request=is_pull_request,
        item_type="pull_request" if is_pull_request else "issue",
        item_type_label="pull request" if is_pull_request else "issue",
        item_type_plural="pull requests" if is_pull_request else "issues",
        action=str(event.get("action") or ""),
        sender=((event.get("sender") or {}).get("login") or "").strip(),
        sender_association=sender_association,
        author=((payload_item.get("user") or {}).get("login") or "").strip(),
        author_association=str(payload_item.get("author_association") or "").upper(),
        title=str(payload_item.get("title") or ""),
        body=str(payload_item.get("body") or ""),
    )
