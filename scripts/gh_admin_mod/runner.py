from gh_admin_mod.context import load_context
from gh_admin_mod.env import get_env, parse_bool, parse_upper_set
from gh_admin_mod.features import automode, blocklist
from gh_admin_mod.github_api import add_labels, close_item, create_comment, lock_item
from gh_admin_mod.logging import fail, notice
from gh_admin_mod.models import FeatureResult
from gh_admin_mod.outputs import set_output


def _init_outputs() -> None:
    set_output("blocked", "false")
    set_output("blocked-user", "")
    set_output("item-type", "")
    set_output("matched-feature", "")
    set_output("match-reason", "")


def _dedupe_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        if not label or label in seen:
            continue
        seen.add(label)
        result.append(label)
    return result


def _set_match_outputs(result: FeatureResult) -> None:
    set_output("matched-feature", result.feature)
    set_output("match-reason", result.reason)
    if result.feature == "blocklist":
        set_output("blocked", "true")
        set_output("blocked-user", result.blocked_user)


def main() -> None:
    _init_outputs()
    context = load_context()
    set_output("item-type", context.item_type)

    if not context.author:
        notice(f"Skipping {context.item_type_label} because no author login was found.")
        return

    exempt_associations = parse_upper_set(get_env("INPUT_EXEMPT_ASSOCIATIONS", ""))
    if context.author_association and context.author_association in exempt_associations:
        notice(
            f"Skipping @{context.author} because author association "
            f"{context.author_association} is exempt."
        )
        return

    result = blocklist.evaluate(context)
    if not result.matched:
        result = automode.evaluate(context)

    if not result.matched:
        notice(f"No moderation feature matched for @{context.author}.")
        return

    _set_match_outputs(result)

    if parse_bool(get_env("INPUT_DRY_RUN", "false")):
        notice(
            f"Dry run: feature {result.feature} would close this "
            f"{context.item_type_label} from @{context.author}."
        )
        return

    global_label = get_env("INPUT_ADD_LABEL", "").strip()
    labels = _dedupe_labels(([global_label] if global_label else []) + result.labels)

    if result.comment_message:
        create_comment(context, result.comment_message)

    if labels:
        add_labels(context, labels)

    close_item(context, get_env("INPUT_CLOSE_REASON", "not_planned"))

    should_lock = parse_bool(get_env("INPUT_LOCK_CONVERSATION", "false")) or result.lock_conversation
    if should_lock:
        lock_item(context)

    notice(
        f"Closed {context.item_type_label} #{context.issue_number} from "
        f"@{context.author} using feature {result.feature}."
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        fail(str(exc))
