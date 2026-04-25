from gh_admin_mod.env import get_env, parse_bool
from gh_admin_mod.github_api import count_open_items
from gh_admin_mod.models import FeatureResult, ModerationContext
from gh_admin_mod.templates import render_template


def _parse_limits(raw_limits: str) -> dict[str, int]:
    limits: dict[str, int] = {}
    for part in raw_limits.split(","):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        try:
            limits[key.strip().upper()] = int(val.strip())
        except ValueError:
            continue
    return limits


def evaluate(context: ModerationContext) -> FeatureResult:
    if not parse_bool(get_env("INPUT_CONCURRENCY_ENABLED", "false")):
        return FeatureResult(matched=False)

    raw_limits = get_env(
        "INPUT_CONCURRENCY_LIMITS",
        "NONE=1,FIRST_TIMER=1,FIRST_TIME_CONTRIBUTOR=1,CONTRIBUTOR=10,COLLABORATOR=10,MEMBER=10",
    )
    limits = _parse_limits(raw_limits)

    limit = limits.get(context.author_association.upper())

    # If limit is 0, it means unlimited. If None, no limit defined for this association.
    if limit is None or limit <= 0:
        return FeatureResult(matched=False)

    current_count = count_open_items(context, context.author, context.item_type)

    if current_count <= limit:
        return FeatureResult(matched=False)

    result = FeatureResult(
        matched=True,
        feature="concurrency",
        reason=(
            f"@{context.author} has {current_count} open {context.item_type_plural}, "
            f"exceeding the limit of {limit} for {context.author_association}."
        ),
        metadata={
            "limit": str(limit),
            "count": str(current_count),
        },
    )

    default_comment = (
        "This {type} was automatically closed because @{user} already has "
        "{count} open {type_plural}, exceeding the allowed limit of {limit}."
    )
    comment_template = get_env("INPUT_CONCURRENCY_COMMENT_MESSAGE", default_comment)
    result.comment_message = render_template(comment_template, context, result)

    return result
