# gh-admin-mod

`gh-admin-mod` is a reusable GitHub Action for repository moderation. The code is split into feature modules so you can keep adding moderation behavior without turning one script into a mess.

## Features

- Blocks users listed in `blockedUser.md` or any other file you configure.
- Supports `concurrency-enabled` to limit the number of open issues or PRs per user based on association.
- Supports `auto-mod` to automatically close suspicious issues and PRs from new contributors.
- Can block issues, pull requests, or both.
- Posts configurable comments before closing items.
- Optionally adds labels and locks conversations.
- Exempts trusted author associations like `OWNER`, `MEMBER`, or `COLLABORATOR`.
- Supports `dry-run` for testing rules without closing anything.

## Blocked users file

By default the action reads `blockedUser.md` from the repository root. Keep it as a simple list with one username per line.

```md
@mike
@repeat-offender
badactor123
```

Lines starting with `#` are ignored.

## Auto-mod

`auto-mod` is a simple built-in moderation feature for suspicious content. When enabled, it checks the issue or PR title/body for:

- configured keywords or phrases
- too many links

By default it only applies to `NONE`, `FIRST_TIMER`, and `FIRST_TIME_CONTRIBUTOR` authors. That keeps it focused on new contributors instead of maintainers and established collaborators.

## Concurrency limits

The `concurrency` feature prevents users from opening too many items at once. When enabled, it counts the user's currently open issues (or PRs) and closes the new one if they have reached their limit.

Limits are defined per GitHub author association. By default:
- `NONE`, `FIRST_TIMER`, `FIRST_TIME_CONTRIBUTOR`: 1 open item
- `CONTRIBUTOR`, `COLLABORATOR`, `MEMBER`: 10 open items
- `OWNER`: unlimited (0)

You can customize these by providing a comma-separated list of `KEY=VALUE` pairs.

## Usage

Check out the repository first so the action can read your blocklist file when the blocklist feature is enabled.

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
          auto-mod: "true"
          add-label: moderated
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
| `exempt-associations` | `OWNER,MEMBER,COLLABORATOR` | Comma-separated author associations that bypass all moderation features. |
| `comment-message` | see `action.yml` | Comment template used by the blocklist feature. Supports `{user}`, `{type}`, `{type_plural}`, `{author_association}`, `{reason}`. |
| `add-label` | `""` | Optional label added for any moderation action. |
| `lock-conversation` | `"false"` | Lock the issue or pull request after closing it. |
| `close-reason` | `not_planned` | Issue close reason. Ignored for pull requests. |
| `dry-run` | `"false"` | Detect matches without commenting or closing anything. |
| `auto-mod` | `"false"` | Enable suspicious-content auto moderation. |
| `auto-mod-keywords` | `telegram,whatsapp,t.me,airdrop,bonus,dm me,contact me,investment opportunity` | Comma-separated phrases checked against the title and body. |
| `auto-mod-max-links` | `"3"` | Link-count threshold for auto moderation. Set `0` to disable link counting. |
| `auto-mod-new-contributors-only` | `"true"` | Restrict auto-mod to `NONE`, `FIRST_TIMER`, and `FIRST_TIME_CONTRIBUTOR`. |
| `auto-mod-comment-message` | see `action.yml` | Comment template used by auto-mod. Supports `{user}`, `{type}`, `{type_plural}`, `{author_association}`, `{reason}`, `{keywords}`, `{link_count}`. |
| `auto-mod-label` | `auto-moderated` | Extra label applied when auto-mod matches. |
| `concurrency-enabled` | `"false"` | Enable association-based concurrency limits. |
| `concurrency-limits` | see `action.yml` | Association-based limits (e.g., `NONE=1,CONTRIBUTOR=10`). Value `0` is unlimited. |
| `concurrency-comment-message` | see `action.yml` | Comment template used by concurrency. Supports `{limit}`, `{count}` and standard placeholders. |

## Outputs

| Output | Description |
| --- | --- |
| `blocked` | `true` when the blocklist feature matched the author. |
| `blocked-user` | The username that matched the blocklist. |
| `item-type` | `issue` or `pull_request`. |
| `matched-feature` | The feature that matched, such as `blocklist` or `auto-mod`. |
| `match-reason` | The reason returned by the matched feature. |

## Examples

Block only issues:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    block-issues: "true"
    block-prs: "false"
```

Custom blocklist comment and alternate blocklist file:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    blocked-users-file: .github/mod/blockedUser.md
    comment-message: >
      @{user} is not allowed to open {type_plural} here.
      This {type} has been closed automatically.
```

Enable auto-mod with custom heuristics:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    auto-mod: "true"
    auto-mod-keywords: telegram,whatsapp,forex,airdrop,dm me
    auto-mod-max-links: "2"
    auto-mod-label: suspicious
```

Use auto-mod only:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    block-issues: "false"
    block-prs: "false"
    auto-mod: "true"
```

Dry run:

```yaml
- uses: Bashamega/gh-admin-mod@v1
  with:
    dry-run: "true"
```

## Project layout

- [action.yml](./action.yml) keeps the GitHub Action inputs and runner wiring.
- [scripts/mod.py](./scripts/mod.py) is the entry point.
- [scripts/gh_admin_mod/runner.py](./scripts/gh_admin_mod/runner.py) handles orchestration.
- [scripts/gh_admin_mod/features/blocklist.py](./scripts/gh_admin_mod/features/blocklist.py) contains the blocklist feature.
- [scripts/gh_admin_mod/features/concurrency.py](./scripts/gh_admin_mod/features/concurrency.py) contains the concurrency limit feature.
- [scripts/gh_admin_mod/features/automod.py](./scripts/gh_admin_mod/features/automod.py) contains the auto-mod feature.

## Notes

- `pull_request_target` is recommended for pull request moderation because it runs with the base repository context and can close PRs from forks.
- The action only moderates newly opened or reopened issues and pull requests.
- Feature order is currently `blocklist` -> `concurrency` -> `auto-mod`. The first matching feature takes the action.
- If you want only `auto-mod`, disable `block-issues` and `block-prs` or provide a `blockedUser.md` file.
