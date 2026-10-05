---
name: comment-tune
description: >
  Tune code comments in the current diff or given files: trim noise, fill in
  missing context, fix comments the code no longer matches. Reports a verdict
  per comment and applies only after approval. Never changes code. Use when
  the user says "comment-tune", "clean up comments", "tune the comments",
  "fix stale comments", or asks to review comments before committing.
---

# comment-tune

Tune comments in one pass: **trim** the noise, **fill** missing context,
**fix** what has gone stale. Comments only. Code logic is never touched.

## Arguments

- No path: the current diff (`git diff HEAD` plus untracked files). Judge only
  comments on changed lines, and fill spots inside changed hunks.
- `PATH...`: those files or directories, every comment in them.
- `--trim-only`, `--fill-only`, `--fix-only`: narrow what is judged.
- `--apply`: skip the approval step (for scripts and CI).

## Steps

1. **Read the rules once.** Read `references/criteria.md`. Read
   `references/examples.md` only if a call is close.
2. **Collect the scope.** For the default diff, run `git diff HEAD -U3` and
   `git ls-files --others --exclude-standard`. Skip generated and vendored
   files (see Untouchable in the criteria).
3. **One pass per file.** Read each file once. For every comment in scope run
   the ordered checks from the criteria, then look for fill spots. Do not
   re-read a file to judge a second category.
4. **Look for evidence before any `add`.** Run
   `git log --no-patch --format='%h %B' -L<start>,<end>:<file>` on the lines
   and read the full message bodies, not just the subjects. Also check
   nearby tests and config. No evidence means `add (needs input)`, never an
   invented reason.
5. **Report** (format below) and stop. Wait for approval unless `--apply`.
   The user may approve all, approve by number, or edit a proposal.
6. **Apply** the approved items:
   - Before editing: `python3 <dir>/scripts/comment_guard.py snapshot FILE...`,
     where `<dir>` is the directory this SKILL.md was loaded from. Windows
     often has no `python3`; try `py -3`, then `python`, before giving up.
     A file it reports as `unchecked (reason)` uses syntax the guard can't
     read safely: check that file's `git diff` yourself after editing, and
     say so in the report.
   - Edit comments only.
   - After editing: `<python> <dir>/scripts/comment_guard.py verify`, with
     the same interpreter. If it reports `CODE CHANGED`, revert that file's
     edits and redo them. With no Python at all, check `git diff` yourself:
     only comment lines may differ.
7. **Finish** with the commit message draft and one line of totals.

## Report format

```
## comment-tune: 3 files, 14 comments judged

src/order/OrderService.java
 1. L42  remove   trim/narration   "Updated to use new client as requested"
 2. L57  rewrite  trim/verbose     5 lines → "// Discount applies after tax (accounting rule)."
 3. L88  rewrite  fix/stale        says "returns null", returns Optional → "// Empty if not found."
 4. L103 add      fill/magic-number   "// Stripe allows 4 req/s per account; 250 ms stays under it."  (from git log a1b2c3d)
 5. L120 add?     fill/magic-number   needs input: where does the 500-item cap come from?
    kept 6: L12 L19 L30 L61 L77 L95

Commit message draft (from removed comments):
  Use withRetry for message sends
  Load data once in initState instead of on every build

Apply 1-4? (all / numbers / edit N)
```

- One line per item: number, line, verdict, `category/tag`, short reason or
  the quoted comment, then `→` and the proposal.
- `kept` lists line numbers only. Untouchable comments are not listed.
- `add?` items are questions. Never apply them until the user answers.
- Leave out the commit draft section when nothing useful was removed.
- Nothing to change: say so in one line and stop.

## Never

- Change code, imports, formatting outside comments, or file layout.
- Touch the untouchable list in the criteria.
- Invent a reason, issue number, owner or source for a comment.
- Judge comments outside the scope you were given.
