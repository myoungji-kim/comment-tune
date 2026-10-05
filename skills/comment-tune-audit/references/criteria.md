# Judgment criteria

One pass per file. For every comment in scope decide **keep**, **remove**,
**rewrite** or **add**, tag it, and give a reason of a few words.

## Order of checks

Run these in order for each existing comment and stop at the first that hits.

1. **Untouchable?** → keep, and leave it out of the report.
2. **Does it contradict the code?** → `fix`: rewrite it to match the code, or
   remove it if the true version would be a trim.
3. **Does it say anything the code can't?**
   - Nothing → `trim`: remove.
   - Partly → `trim`: rewrite down to every part that matters, cutting only
     what the code already says.
4. **Otherwise** → keep.

Then look at the code in scope for **fill** spots that have no comment.

## trim — remove or shorten

| tag | what it looks like |
|---|---|
| `restates` | Says what the next line says. `// increment count`, `/** Gets the user. */` on a private `getUser()` |
| `narration` | Describes the edit, not the code. "added", "updated", "now uses", "new", "as requested", "per review", "fixed bug where" |
| `history` | The author's reason for a change, or what the code used to do. "we switched from X because", "previously", "used to", "the old version" |
| `verbose` | One useful point buried in lines that restate the code or repeat themselves. Rewrite to that point, one line. Not verbose when each line adds its own fact: a reason, an example, an edge case, a link |
| `dead-code` | Commented-out code. Version control keeps it |
| `banner` | Decorative lines and section headers: `// ======`, `// ---- Helpers ----` |
| `bare-todo` | TODO/FIXME with no reason, owner, issue or trigger |

`history` and `narration` often carry something worth keeping. Move that part
to the commit message draft instead of dropping it.

A TODO that says what to do *and* why or when (`TODO(#123): drop once the
v1 API is retired`) is a keep.

Not `restates`: a comment that says what an unclear call into a library you
can't change does (`buf.flip(); // switch to read mode`). Keep it.

## fill — add what is missing

Add a comment only when the code has one of these **and** you can state the
reason from evidence:

| tag | trigger in the code |
|---|---|
| `constraint` | Behaviour forced by something outside the code: an API limit, a spec, a legal rule, a platform quirk |
| `workaround` | Code that looks wrong or roundabout on purpose: a retry, a sleep, a double call, a disabled check |
| `rationale` | A choice where the obvious alternative was rejected: a slower algorithm, a copy instead of a reference, a lock |
| `trap` | Something that breaks if moved or "simplified": call order, thread confinement, a cache that must be cleared, an O(n²) on a known-small input |
| `magic-number` | A literal whose value came from somewhere: a timeout, a size limit, a rate, a status code |
| `api-contract` | A public function whose contract is not obvious from its signature: nullability, units, thrown errors, ownership. Keep it short |

**Evidence** means the code, nearby tests, config, the diff, `git log` or
`git blame` on those lines, or an issue linked from them. Never invent a
reason. If the trigger is there but the reason isn't, report it as
`add (needs input)` with the question to ask, and leave the code untouched.

Do not add comments to code that is plain: a getter, a straightforward loop,
a well-named call.

## fix — make it true

| tag | what it looks like |
|---|---|
| `stale` | The comment and the code disagree: wrong parameter names, wrong return value, wrong number, wrong behaviour, a reference to code that is gone |

Trust the code, not the comment. If you can't tell which one is the bug, keep
the comment, flag it as `stale?` in the report, and say what disagrees. Never
change the code to match the comment.

## Untouchable

Never remove or rewrite:

- License and copyright headers.
- Linter, formatter, compiler and tooling directives: `eslint-disable`,
  `@ts-ignore`, `@ts-expect-error`, `// ignore:` (Dart), `// ignore_for_file:`,
  `@SuppressWarnings`, `//noinspection`, `#pragma`, `// prettier-ignore`,
  `// istanbul ignore`, `//go:build`, `# type: ignore`, `# noqa`, shebangs,
  encoding lines.
- Generated files: headers like `GENERATED CODE - DO NOT MODIFY`, `@generated`,
  and files such as `*.g.dart`, `*.freezed.dart`, `*.pb.*`, `*_pb2.py`,
  build output and vendored code.
- Doc comments on public API, which IDEs and doc tools show to callers, even
  when they only restate the name; fix them if stale, never remove them. On
  non-public code a doc comment that only restates the name is `restates`.
- Comments the user explicitly asked for.

## Rewrites

- One line by default. Present tense. Describe the code, not the edit.
- Never drop a fact the original gave that the code can't show: a reason,
  an example, an edge case, a version, a link. If they don't fit on one
  line, use more lines; if shortening would lose one, keep the original.
- Keep the comment's original style (`//` vs `/* */` vs `///` vs Javadoc).
- Keep the language of the codebase's existing comments.
- Put a comment directly above the line it explains, not at the end of a
  long line.
