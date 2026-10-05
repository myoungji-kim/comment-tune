# oss-php-psr7-caching-stream labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 9 | keep | api-contract | Stream decorator that can cache previously read bytes fr... | public class doc |
| 18 | keep | untouchable | @var StreamInterface Stream being wrapped | property type info |
| 21 | keep | untouchable | @var int Number of bytes to skip reading due to a write... | property type info |
| 30 | keep | api-contract | We will treat the buffer object as the body of the strea... | constructor doc, target requirements |
| 78 | keep | trap | Discovering the size reads the remote stream to EOF and... | why the cursor is restored |
| 101 | remove | restates | Read the remoteStream until we have read in at least the... | the while condition says it |
| 116 | ambiguous | - | We can just do a normal seek since we've already seen th... | see below |
| 127 | remove | restates | Perform a regular read on any previously read data from... | the next line says it |
| 131 | remove | restates | More data was requested so read from the remote stream | the `if ($remaining)` says it |
| 133 | keep | rationale | If data was written to the buffer in a position that wou... | why bytes are skipped |
| 151 | keep | rationale | A short cache write would silently corrupt later replays... | why the check throws |
| 162 | rewrite | verbose | When appending to the end of the currently read stream,... | last sentence repeats the first; keep the rest |
| 196 | keep | api-contract | Close the remote stream and any attached cache stream. | public doc, cache closed only if attached |

Lines 78-80, 101-102, 133-136 and 162-165 are consecutive line comments, so
the scorer merges each run into one comment.

## Ambiguous, not scored

- 116 `We can just do a normal seek since we've already seen this byte.`: the
  `else` of `$diff > 0` already implies the byte is cached, but the comment
  names that reason in plain words; keep or remove are both defensible.
