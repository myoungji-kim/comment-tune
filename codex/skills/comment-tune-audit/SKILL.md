---
name: comment-tune-audit
description: >
  Read-only comment health check for a whole repository or directory: counts
  noise, stale and missing-context comments by type, ranks the worst files,
  and lists spots that likely need a comment. Never edits files. Use when the
  user says "comment-tune-audit", "audit the comments", "how bad are the
  comments in this repo", or wants to know where to run comment-tune first.
---

# comment-tune-audit

Repo-wide report on comment quality. Read-only: no file is edited.

## Arguments

- No path: the whole repository (`git ls-files`).
- `PATH...`: those directories or files only.

## Steps

1. **Read the rules once.** Read `references/criteria.md` and
   `references/patterns.md`.
2. **List the files.** `git ls-files` for the scope, minus the excludes in the
   patterns reference. Note the total count of source files.
3. **Grep first.** Run each trim and fill pattern from the patterns reference
   over the scope with `git grep -nIE` (or `rg -n`). Collect hits per file
   and per tag. This is cheap; do it for everything.
4. **Read selectively.** Read the files with the most hits, plus a spread of
   the rest, up to about 30 files or what the context comfortably allows. In
   each, judge every comment with the criteria (trim, fill, fix in the same
   pass). Grep can't find `restates`, `verbose` or `stale`; only reading can.
5. **Report** (format below). Counts from files you did not read are grep
   estimates; say so.

## Report format

```
## comment-tune-audit: 214 source files, 41 read

| type | tag | count |
|---|---|---|
| trim | narration | 37 |
| trim | restates | 22 (read files only) |
| trim | dead-code | 15 |
| fix  | stale | 6 (read files only) |
| fill | magic-number | 11 |
...

Worst files
 1. src/billing/InvoiceService.java   18 noise, 2 stale
 2. lib/data/sync_repository.dart     11 noise, 1 missing context
...

Likely missing context
 - lib/data/sync_repository.dart:88   Future.delayed(800 ms) with no reason
 - src/api/client.ts:41               empty catch swallows errors
...

Stale comments
 - src/order/OrderService.java:88     says "returns null", returns Optional

Next: $comment-tune src/billing lib/data
```

- Up to 10 worst files, ranked by noise + stale, then missing context.
- Up to 15 missing-context spots and every stale comment you found, each
  with `path:line` and a few words.
- End with the `comment-tune` command that would fix the worst files.
- Don't print proposals for every comment; that's what `comment-tune` is for.

## Never

- Edit, create or delete files.
- Report generated or vendored files.
