import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def normalize_user(value: str) -> str:
    return value.strip().lstrip("@").lower()


def parse_list(value: str) -> set[str]:
    return {item.strip().upper() for item in value.split(",") if item.strip()}


def set_output(name: str, value: str) -> None:
    output_path = get_env("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def notice(message: str) -> None:
    print(f"::notice::{message}")


def fail(message: str) -> None:
    print(f"::error::{message}")
    raise SystemExit(1)


def load_event() -> dict:
    event_path = get_env("GITHUB_EVENT_PATH")
    if not event_path:
        fail("GITHUB_EVENT_PATH is not available.")

    with open(event_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_blocked_users(blocked_users_file: str) -> set[str]:
    workspace = get_env("GITHUB_WORKSPACE")
    if not workspace:
        fail("GITHUB_WORKSPACE is not available.")

    blocklist_path = Path(workspace, blocked_users_file).resolve()
    if not blocklist_path.exists():
        fail(
            f"Blocked users file not found at {blocked_users_file}. "
            "Make sure the repository is checked out before this action runs."
        )

    blocked_users: set[str] = set()
    with open(blocklist_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            blocked_users.add(normalize_user(line))

    return blocked_users


def api_request(method: str, url: str, payload: dict | None = None) -> dict | None:
    token = get_env("GITHUB_TOKEN")
    if not token:
        fail("GITHUB_TOKEN is not available.")

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

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


def main() -> None:
    set_output("blocked", "false")
    set_output("blocked-user", "")
    set_output("item-type", "")

    event = load_event()
    issue = event.get("issue")
    pull_request = event.get("pull_request")
    payload_item = issue or pull_request

    if not payload_item:
        fail("This action only supports issue and pull request events.")

    is_pull_request = pull_request is not None
    item_type = "pull_request" if is_pull_request else "issue"
    item_type_label = "pull request" if is_pull_request else "issue"
    item_type_plural = "pull requests" if is_pull_request else "issues"

    set_output("item-type", item_type)

    author = ((payload_item.get("user") or {}).get("login") or "").strip()
    author_association = str(payload_item.get("author_association") or "").upper()

    if not author:
        notice(f"Skipping {item_type_label} because no author login was found.")
        return

    if is_pull_request and not parse_bool(get_env("INPUT_BLOCK_PRS", "true")):
        notice("Pull request blocking is disabled.")
        return

    if not is_pull_request and not parse_bool(get_env("INPUT_BLOCK_ISSUES", "true")):
        notice("Issue blocking is disabled.")
        return

    exempt_associations = parse_list(get_env("INPUT_EXEMPT_ASSOCIATIONS", ""))
    if author_association and author_association in exempt_associations:
        notice(f"Skipping @{author} because author association {author_association} is exempt.")
        return

    blocked_users = load_blocked_users(get_env("INPUT_BLOCKED_USERS_FILE", "blockedUser.md"))
    normalized_author = normalize_user(author)

    if normalized_author not in blocked_users:
        notice(f"@{author} is not present in the blocked users file.")
        return

    set_output("blocked", "true")
    set_output("blocked-user", author)

    if parse_bool(get_env("INPUT_DRY_RUN", "false")):
        notice(f"Dry run: would close this {item_type_label} from @{author}.")
        return

    repo = get_env("GITHUB_REPOSITORY")
    if "/" not in repo:
        fail("GITHUB_REPOSITORY is not available.")
    owner, repo_name = repo.split("/", 1)
    issue_number = payload_item["number"]
    base_api = f"https://api.github.com/repos/{owner}/{repo_name}"

    comment_message = (
        get_env("INPUT_COMMENT_MESSAGE", "")
        .replace("{user}", author)
        .replace("{type}", item_type_label)
        .replace("{type_plural}", item_type_plural)
        .replace("{author_association}", author_association or "NONE")
        .strip()
    )

    if comment_message:
        api_request(
            "POST",
            f"{base_api}/issues/{issue_number}/comments",
            {"body": comment_message},
        )

    add_label = get_env("INPUT_ADD_LABEL", "").strip()
    if add_label:
        api_request(
            "POST",
            f"{base_api}/issues/{issue_number}/labels",
            {"labels": [add_label]},
        )

    if is_pull_request:
        api_request(
            "PATCH",
            f"{base_api}/pulls/{issue_number}",
            {"state": "closed"},
        )
    else:
        api_request(
            "PATCH",
            f"{base_api}/issues/{issue_number}",
            {
                "state": "closed",
                "state_reason": get_env("INPUT_CLOSE_REASON", "not_planned"),
            },
        )

    if parse_bool(get_env("INPUT_LOCK_CONVERSATION", "false")):
        api_request(
            "PUT",
            f"{base_api}/issues/{issue_number}/lock",
            {"lock_reason": "resolved"},
        )

    notice(f"Closed {item_type_label} #{issue_number} from blocked user @{author}.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        fail(str(exc))
