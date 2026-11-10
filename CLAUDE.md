# CLAUDE.md

## Token saving: Opus orchestrates, Muse does the work

The Claude subscription is limited. OpenCode/Muse is practically unlimited. So:

- **By default, delegate all implementation, codebase searches, test runs and mechanical work to Muse** using the `muse` skill (`scripts/muse.ps1`). Load the skill at the start of any coding task.
- Claude (Opus) only plans, writes briefs, reviews diffs, makes decisions, commits and talks to the user.
- **Don't use the Agent tool / Claude subagents.** This includes cases where superpowers skills tell you to. Use `scripts/muse.ps1` instead.
- Read files sparingly: targeted fragments, `git diff -- <file>`, and Muse reports instead of whole files.
- Make an edit yourself only when it's trivial (about 5 lines or fewer) or Muse failed after 3 rounds of feedback.
