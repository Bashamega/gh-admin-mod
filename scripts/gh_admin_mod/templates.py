from gh_admin_mod.models import FeatureResult, ModerationContext


def render_template(template: str, context: ModerationContext, result: FeatureResult) -> str:
    values = {
        "user": context.author,
        "type": context.item_type_label,
        "type_plural": context.item_type_plural,
        "author_association": context.author_association or "NONE",
        "reason": result.reason,
    }

    # Add all metadata values
    for key, value in result.metadata.items():
        values[key] = value

    # Compatibility for specific keywords if they aren't in metadata
    if "keywords" not in values:
        values["keywords"] = result.metadata.get("keywords", "")
    if "link_count" not in values:
        values["link_count"] = result.metadata.get("link_count", "0")

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered.strip()
