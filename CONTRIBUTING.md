# Contributing

Bull Desk is instructions, not software: the deliverable is prose and copy-pasteable commands that a Bot can follow. Contributions should keep that shape.

- One skill per directory under `skills/`, one `SKILL.md` each, body under 320 lines, frontmatter with `name`, `description`, `license: MIT` and `metadata`.
- Agents under `agents/` keep the three-part shape: frontmatter, Bot profile card, full system prompt.
- Every write path says who may use it and under what approval. Every command is copy-pasteable and self-contained.
- No emoji, no return claims, no strategy content.
- Run `scripts/check.sh` before proposing changes; it lints frontmatter, links, the one-writer rule and leftover references to the original exchange.
- Verify any Webull API claim against https://developer.webull.com/apis/docs/ and note the date you checked.
