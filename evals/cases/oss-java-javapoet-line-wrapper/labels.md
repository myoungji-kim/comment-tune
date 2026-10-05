# oss-java-javapoet-line-wrapper labels

Lines refer to input/LineWrapper.java. Lines 67-68 merge into one comment.

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 1 | keep | untouchable | Copyright (C) 2016 Square, Inc. Licensed under the Apache Lic | license header |
| 22 | keep | api-contract | Implements soft line wrapping on an appendable. To use, appe | class usage doc |
| 32 | ambiguous | - | Characters written since the last wrapping space that haven't | useful field doc, no clean tag |
| 35 | ambiguous | - | The number of characters since the most recent newline. Inclu | useful invariant, no clean tag |
| 38 | keep | magic-number | -1 if we have no buffering; otherwise the number of {@code in | -1 sentinel |
| 43 | keep | api-contract | Null if we have no buffering; otherwise the type to pass to t | nullability |
| 55 | keep | api-contract | @return the last emitted char or {@link Character#MIN_VALUE} | sentinel return |
| 60 | keep | api-contract | Emit {@code s}. This may be buffered to permit line wraps to b | buffering behaviour |
| 67-68 | keep | rationale | If s doesn't cause the current line to cross the limit, buffe | why buffer: wrap decided later |
| 75 | ambiguous | - | Wrap if appending s would overflow the current line. | restates the boolean, but decodes it |
| 87 | keep | api-contract | Emit either a space or a newline character. | method doc |
| 92 | keep | trap | Increment the column even though the space is deferred to nex | column counts a deferred space |
| 97 | keep | api-contract | Emit a newline character if the line will exceed it's limit, o | method doc |
| 107 | keep | api-contract | Flush any outstanding text and forbid future writes to this li | method doc |
| 113 | fix | stale | Write the space followed by any buffered text that follows it. | WRAP writes newline+indent, EMPTY writes nothing |
| 143 | keep | api-contract | A delegating {@link Appendable} that records info about the ch | class doc |

## Ambiguous, not scored

- 32, 35: private field docs that are worth keeping but fit no context tag well (35's "Includes both out and the buffer" is close to a trap).
- 75: restates `boolean wrap = ...`, yet makes the compound condition readable; either keep or remove is defensible.
