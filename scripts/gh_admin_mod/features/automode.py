import re

from gh_admin_mod.env import get_env, parse_bool, parse_csv, parse_int
from gh_admin_mod.models import FeatureResult, ModerationContext
from gh_admin_mod.templates import render_template

NEW_CONTRIBUTOR_ASSOCIATIONS = {"NONE", "FIRST_TIMER", "FIRST_TIME_CONTRIBUTOR"}
LINK_PATTERN = re.compile(r"(https?://|www\.)", re.IGNORECASE)


def _content(context: ModerationContext) -> str:
    return f"{context.title}\n{context.body}".strip()


def evaluate(context: ModerationContext) -> FeatureResult:
    if not parse_bool(get_env("INPUT_AUTO_MODE", "false")):
        return FeatureResult(matched=False)

    if parse_bool(get_env("INPUT_AUTO_MODE_NEW_CONTRIBUTORS_ONLY", "true")):
        if context.author_association not in NEW_CONTRIBUTOR_ASSOCIATIONS:
            return FeatureResult(matched=False)

    content = _content(context)
    lowered = content.lower()
    keywords = [
        keyword
        for keyword in parse_csv(get_env("INPUT_AUTO_MODE_KEYWORDS", ""))
        if keyword.lower() in lowered
    ]
    max_links = parse_int(get_env("INPUT_AUTO_MODE_MAX_LINKS", "3"), 3)
    link_count = len(LINK_PATTERN.findall(content))

    reasons: list[str] = []
    if keywords:
        reasons.append(f"matched keywords: {', '.join(keywords)}")
    if max_links > 0 and link_count >= max_links:
        reasons.append(f"contains {link_count} links (threshold: {max_links})")

    if not reasons:
        return FeatureResult(matched=False)

    result = FeatureResult(
        matched=True,
        feature="auto-mode",
        reason="; ".join(reasons),
        labels=[get_env("INPUT_AUTO_MODE_LABEL", "").strip()],
        metadata={
            "keywords": ", ".join(keywords),
            "link_count": str(link_count),
        },
    )
    result.labels = [label for label in result.labels if label]
    result.comment_message = render_template(
        get_env("INPUT_AUTO_MODE_COMMENT_MESSAGE", ""),
        context,
        result,
    )
    return result
