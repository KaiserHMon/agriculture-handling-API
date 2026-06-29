# Skill Registry

This registry lists all available global and project-level skills, as well as project convention files.

## Project Convention Files

- [agent.md](file:///C:/Proyectos/Api-AgricultureHandling/agent.md) — Coding style, structure, testing guidelines, FastAPI best practices, and pre-delivery checklist.
- [agents/gemini.md](file:///C:/Proyectos/Api-AgricultureHandling/agents/gemini.md) — Detailed project context, architecture (routers/services/repositories layered flow, transaction boundary rules), directory mapping, key commands, and FastAPI/Pydantic/DB conventions.

## Skills

| Name | Trigger / Description | Path | Scope |
| ---- | --------------------- | ---- | ----- |
| `branch-pr` | Create Gentle AI pull requests with issue-first checks. Trigger: creating, opening, or preparing PRs for review. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/branch-pr/SKILL.md) | global |
| `chained-pr` | Trigger: PRs over 400 lines, stacked PRs, review slices. Split oversized changes into chained PRs that protect review focus. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/chained-pr/SKILL.md) | global |
| `cognitive-doc-design` | Design docs that reduce cognitive load. Trigger: writing guides, READMEs, RFCs, onboarding, architecture, or review-facing docs. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/cognitive-doc-design/SKILL.md) | global |
| `comment-writer` | Write warm, direct collaboration comments. Trigger: PR feedback, issue replies, reviews, Slack messages, or GitHub comments. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/comment-writer/SKILL.md) | global |
| `go-testing` | Trigger: Go tests, go test coverage, Bubbletea teatest, golden files. Apply focused Go testing patterns. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/go-testing/SKILL.md) | global |
| `issue-creation` | Create Gentle AI issues with issue-first checks. Trigger: creating GitHub issues, bug reports, or feature requests. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/issue-creation/SKILL.md) | global |
| `judgment-day` | Trigger: judgment day, dual review, adversarial review, juzgar. Run blind dual review, fix confirmed issues, then re-judge. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/judgment-day/SKILL.md) | global |
| `skill-creator` | Trigger: new skills, agent instructions, documenting AI usage patterns. Create LLM-first skills with valid frontmatter. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/skill-creator/SKILL.md) | global |
| `skill-improver` | Trigger: improve skills, audit skills, refactor skills, skill quality. Audit and upgrade existing LLM-first skills. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/skill-improver/SKILL.md) | global |
| `work-unit-commits` | Plan commits as reviewable work units. Trigger: implementation, commit splitting, chained PRs, or keeping tests and docs with code. | [SKILL.md](file:///C:/Users/ASUS/.gemini/antigravity-cli/skills/work-unit-commits/SKILL.md) | global |
