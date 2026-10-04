# comment-tune

Applies whenever you write or edit code. A comment is for the next person who
reads the code, not a record of how it got written.

## 1. Comment what the code can't say

- Write a comment only for what the code cannot show: an external constraint,
  a workaround, a non-obvious choice, a trap (ordering, concurrency,
  performance), or where a magic number comes from.
- If a better name or a smaller function would make the comment unnecessary,
  change the code instead.
- Never restate what the next line does.

## 2. Write for the reader, not about your edit

- No narration of your work: "added", "updated", "changed", "now", "new",
  "as requested", "previously", "fixed the bug where".
- Why *you* made a change is history. History belongs in the commit message.
- Describe the code as it stands, for someone who never saw the old version.

## 3. One line, or none

- If deleting the comment would confuse no one, don't write it.
- One line by default. Go longer only for a public API contract or a trap that
  needs the whole story.
- No banners, divider lines, commented-out code, or TODOs without a reason or
  a trigger.

## 4. Keep comments true

- When you change code, fix or delete every comment the change made wrong,
  including doc comments on the function and its callers.
- A wrong comment is worse than no comment.

## Scope

- Outside the lines you are changing, leave existing comments alone unless
  rule 4 applies. Cleanup is what `comment-tune` is for.
- Never touch license headers, linter or compiler directives
  (`eslint-disable`, `@SuppressWarnings`, `// ignore:`, `#pragma`), generated
  files, or comments the user explicitly asked for.
