from dataclasses import dataclass, field


@dataclass
class ModerationContext:
    owner: str
    repo: str
    issue_number: int
    is_pull_request: bool
    item_type: str
    item_type_label: str
    item_type_plural: str
    author: str
    author_association: str
    title: str
    body: str


@dataclass
class FeatureResult:
    matched: bool
    feature: str = ""
    reason: str = ""
    comment_message: str = ""
    labels: list[str] = field(default_factory=list)
    lock_conversation: bool = False
    blocked_user: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
