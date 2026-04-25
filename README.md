# mod

`mod` is a simple reusable GitHub Action for repository moderation. It reads usernames from a simple blocklist file and automatically closes issues or pull requests opened by those users.

## Features

- Blocks users listed in `blockedUser.md` or any other file you configure.
- Can block issues, pull requests, or both.
- Posts a configurable comment before closing the item.
- Optionally adds a label and locks the conversation.
- Lets you exempt trusted author associations like `OWNER`, `MEMBER`, or `COLLABORATOR`.
- Supports a `dry-run` mode so you can verify behavior before enforcing it.
- Keeps the action YAML small by running the moderation logic from Python.

## Blocklist format

By default the action reads `blockedUser.md` from the repository root. The file should contain only usernames, one per line.

Example:

```md
@mike
@repeat-offender
badactor123
```

Lines starting with `#` are ignored, so you can still add comments if you need them.

## Usage

This action needs the repository checked out first so it can read your blocklist file.

```yaml
name: Moderate Issues And PRs

on:
  issues:
    types: [opened, reopened]
  pull_request_target:
    types: [opened, reopened, ready_for_review]

permissions:
  issues: write
  pull-requests: write

jobs:
  mod:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: Bashamega/gh-admin-mod@v1
        with:
          blocked-users-file: blockedUser.md
          block-issues: "true"
          block-prs: "true"
          add-label: blocked-user
```

If you are using the action locally from the same repository:

```yaml
- uses: ./
```

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `blocked-users-file` | `blockedUser.md` | Path to the blocklist file containing one username per line. |
| `block-issues` | `"true"` | Close issues opened by blocked users. |
| `block-prs` | `"true"` | Close pull requests opened by blocked users. |
| `exempt-associations` | `OWNER,MEMBER,COLLABORATOR` | Comma-separated author associations that should bypass blocking. |
| `comment-message` | see `action.yml` | Comment template posted before closing. Supports `{user}`, `{type}`, `{type_plural}`, `{author_association}`. |
| `add-label` | `""` | Optional label to add before closing the issue or pull request. |
| `lock-conversation` | `"false"` | Lock the issue or pull request after closing it. |
| `close-reason` | `not_planned` | Issue close reason. Ignored for pull requests. |
| `dry-run` | `"false"` | Detect matches without commenting or closing anything. |

## Outputs

| Output | Description |
| --- | --- |
| `blocked` | `true` when the author matched the blocklist. |
| `blocked-user` | The username that matched the blocklist. |
| `item-type` | `issue` or `pull_request`. |

## Example configurations

Block only issues:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    block-issues: "true"
    block-prs: "false"
```

Custom comment and alternate blocklist file:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    blocked-users-file: .github/mod/blockedUser.md
    comment-message: >
      @{user} is not allowed to open {type_plural} here.
      This {type} has been closed automatically.
```

Dry run:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    dry-run: "true"
```

## Notes

- `pull_request_target` is recommended for pull request moderation because it runs with the base repository context and can close PRs from forks.
- The action only moderates new or reopened issues and pull requests. It does not block comments, reviews, or other activity.
- The moderation logic lives in [scripts/mod.py](/Users/adam/gh-admin-mod/scripts/mod.py), not inline in `action.yml`.
