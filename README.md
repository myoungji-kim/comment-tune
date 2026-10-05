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

The detailed judgment rules (`rules/references/criteria.md`) follow the
comment chapter of Robert C. Martin's *Clean Code*, with one exception: doc
comments on public API are never removed, even when they only restate the name,
because IDEs and doc tools show them to callers.

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
| audit a repo, read-only | `/comment-tune-audit` |
| audit some directories | `/comment-tune-audit src/ app/` |
| tune the current diff | `/comment-tune` |
| tune paths | `/comment-tune src/order` |
| narrow the scope | `--trim-only`, `--fill-only`, `--fix-only` |
| apply without asking | `--apply` |

Start with the audit, then tune the directories it points to. Tuning a whole
large repo in one run makes a report too long to review.

## Results

Measured with Claude Code in headless mode, the user's own plugins and settings
left out. Scores come from `evals/run.py`; numbers are totals over all runs.

**Against the same model with a plain "clean up the comments" prompt**, on 12
real open-source files, 3 runs each:

| | comment-tune | plain prompt |
|---|---|---|
| comments rewritten or added | 57 | 342 |
| inaccurate or invented statements written (blind judge) | 0 | 9 |
| runs that changed code | 0 | 1 |
| noise comments removed | 61/78 (78%) | 44/78 (56%) |
| comments worth keeping deleted | 2/450 | 0/450 |
| stale comments fixed | 24/27 | 26/27 |

The plain prompt deletes nothing worth keeping, but it rewrites and adds six
times as many comments, and some of those rewrites turn a true comment into a
wrong one. comment-tune changes far less and makes nothing up.

**Current version**, 3 runs per case:

| | 14 real files, 7 languages | 7 seeded cases |
|---|---|---|
| comments worth keeping deleted | 0/522 | 0/69 |
| kept word for word (the rest rewritten in place) | 507/522 | 69/69 |
| noise comments removed | 80/90 | 63/63 |
| stale comments fixed | 26/27 | 17/18 |
| expected context comments added | | 42/42 |
| comment added where none belongs | | 0/21 |
| runs that changed code | 0 | 0 |

Read these with their limits. The labels were drafted with Claude against the
criteria, and the blind judge is also Claude, so both share the model's habits.
The real-code sample is small, and well-kept open-source code has less noise
than most codebases. Borderline comments still get different verdicts from run
to run.

### Cost

- **Always on:** the core rules add about 460 tokens to each session.
- **Per run, it depends on the edits, not the file size.** With Claude Code's
  default model, one `/comment-tune --apply` on a real file cost $0.17–0.18
  when nothing needed changing (4 turns) and about $0.36 when many comments
  did (16–19 turns). The plain prompt cost $0.19–0.37 on the same four files;
  the averages were $0.27 for both. About 85% of the tokens are cache reads,
  billed at a tenth of fresh input, so raw token counts overstate the cost.

## Safety

- **Edits comments only.** Before applying, the skill snapshots each file's
  comment-free code with `comment_guard.py`; afterwards it verifies the code is
  identical and redoes any file where it is not.
- **Asks first.** It reports every verdict and waits for approval unless you
  pass `--apply`. `comment-tune-audit` never edits.
- **No network, nothing installed.** The session-start hook prints one bundled
  JSON file with `cat`. `comment_guard.py` uses the Python standard library only
  and writes its snapshot inside `.git/` (or the temp directory outside a repo).

## Languages

The skill reads any language. The code-unchanged check knows:

- **Python** through the standard `tokenize` module, docstrings included.
- **PHP** with its own lexer: `#` and `//` comments, `#[...]` attributes,
  heredoc and nowdoc, and inline HTML around `<?php ... ?>`.
- **`//` and `/* */` languages**: Java, Kotlin, Scala, Groovy, Dart, JavaScript,
  TypeScript, Go, C, C++, Objective-C, C#, Swift, Rust, CSS, SCSS, Less.
- **`#` languages**: shell, Ruby, Perl, R, YAML, TOML, properties.

A file that uses syntax the check doesn't model, such as a regex literal with
`//` in it, a raw string, a heredoc or a YAML block scalar, is reported as
`unchecked` instead of passed, and the skill checks that file's diff by hand.

## Layout

```
rules/            single source: core rules, skill bodies, references
scripts/build.py  generates skills/, AGENTS.md, hooks/session-start.json
tools/            comment_guard.py: proves an edit changed comments only
evals/            eval cases, the runner, and a blind judge
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
tag, in six languages. The `oss-*` cases measure how often real comments worth
keeping get deleted. Pick a set with `--case 'oss-*'`.

### Third-party code in the eval cases

The `oss-*` cases hold unmodified source files from cenkalti/backoff,
dart-lang/http, guzzle/guzzle, guzzle/psr7, jhy/jsoup, michaelbull/kotlin-result,
pallets/itsdangerous, sindresorhus/ky and square/javapoet, under their own
MIT, BSD-3-Clause, ISC or Apache-2.0 licenses. Each case folder carries the
project's `LICENSE` and records the source commit and path in `case.json`. These
files are test data only; the plugin itself doesn't use them.

## License

MIT for this project. The third-party files above keep their own licenses.
