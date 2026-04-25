from pathlib import Path

from gh_admin_mod.env import get_env, normalize_user, parse_bool
from gh_admin_mod.logging import fail
from gh_admin_mod.models import FeatureResult, ModerationContext
from gh_admin_mod.templates import render_template


def _load_blocked_users(blocked_users_file: str) -> set[str]:
    workspace = get_env("GITHUB_WORKSPACE")
    if not workspace:
        fail("GITHUB_WORKSPACE is not available.")

    blocklist_path = Path(workspace, blocked_users_file).resolve()
    if not blocklist_path.exists():
        fail(
            f"Blocked users file not found at {blocklist_path}. "
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


def evaluate(context: ModerationContext) -> FeatureResult:
    if context.is_pull_request and not parse_bool(get_env("INPUT_BLOCK_PRS", "true")):
        return FeatureResult(matched=False)

    if not context.is_pull_request and not parse_bool(get_env("INPUT_BLOCK_ISSUES", "true")):
        return FeatureResult(matched=False)

    blocked_users = _load_blocked_users(get_env("INPUT_BLOCKED_USERS_FILE", "blockedUser.md"))
    normalized_author = normalize_user(context.author)

    if normalized_author not in blocked_users:
        return FeatureResult(matched=False)

    result = FeatureResult(
        matched=True,
        feature="blocklist",
        reason=f"@{context.author} is listed in the blocked users file.",
        blocked_user=context.author,
    )
    result.comment_message = render_template(get_env("INPUT_COMMENT_MESSAGE", ""), context, result)
    return result
