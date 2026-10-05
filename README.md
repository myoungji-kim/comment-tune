# comment-tune

Cut the noise. Keep the context.

A Claude Code plugin that tunes code comments: trim the noise, fill in
missing context, fix stale ones. It never changes code.

## What you get

- **Core rules, always on.** Four rules (`rules/core.md`, under 50 lines) are
  loaded at session start, so bad comments don't get written in the first place.
- **`comment-tune`.** Judges every comment in the current diff (or given paths)
  in one pass: keep / remove / rewrite / add, with a reason and a proposal.
  Applies only after you approve, then proves no code changed. Anything worth
  keeping from removed comments becomes a commit message draft.
- **`comment-tune-audit`.** Read-only report for a whole repo or directory:
  counts by type, worst files, spots likely missing context.

## The four rules

1. Comment what the code can't say.
2. Write for the reader, not about your edit.
3. One line, or none.
4. Keep comments true.

## Install

```
/plugin marketplace add myoungji-kim/comment-tune
/plugin install comment-tune@comment-tune
```

Without the plugin, copy `AGENTS.md` into your project, or its content into a
`CLAUDE.md`, for the core rules alone.

## Usage

| | command |
|---|---|
| tune the current diff | `/comment-tune` |
| tune paths | `/comment-tune src/order` |
| narrow the scope | `--trim-only`, `--fill-only`, `--fix-only` |
| apply without asking | `--apply` |
| audit a repo | `/comment-tune-audit` |

## Layout

```
rules/            single source: core rules, skill bodies, references
scripts/build.py  generates skills/, AGENTS.md, hooks/session-start.json
tools/            comment_guard.py: proves an edit changed comments only
evals/            seeded cases in six languages, clean-file controls, a runner
tests/            lexer tests
```

Edit `rules/` and `tools/`, then run `python3 scripts/build.py`. CI runs
`python3 scripts/build.py --check`.

## Evals

```
python3 evals/run.py --selftest                       # scorer sanity check, offline
python3 evals/run.py --coverage                       # case items per tag; flags thin spots
python3 evals/run.py --agent claude --arm skill       # real headless runs
python3 evals/run.py --agent claude --arm baseline    # same agent, no plugin
python3 evals/run.py --rescore evals/results/RUN.json # rescore saved outputs
python3 evals/judge.py evals/results/A.json B.json   # blind judge of rewrites and additions
```

Metrics: noise removed, context comments kept verbatim and not deleted (the
pair that matters most; a rewrite in place counts as not deleted),
stale comments fixed, expected comments added, no comments at forbidden
spots (clean code, numbers with no known reason), code changes (must be 0),
tokens. Agent runs take minutes and real tokens each; run them in a sandbox.

Cases come in two sets. The seeded cases are written to cover every criteria
tag. The `oss-*` cases are unmodified files from permissive open-source
projects (source commit and license in each folder) and measure how often
real comments worth keeping get deleted. Their labels are drafts: review each
case's `labels.md` before trusting a score. Pick a set with `--case 'oss-*'`.

## License

MIT
