# oss-java-jsoup-controllable-input labels

Lines refer to input/ControllableInputStream.java. Consecutive line comments are merged (22-31, 35-36, 305-306).

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 16 | keep | api-contract | A jsoup internal class (so don't use it as there is no contra | class doc, internal-use warning |
| 20 | keep | constraint | reimplemented from ConstrainableInputStream for JDK21 - exten | BufferedInputStream pins virtual threads |
| 22-31 | keep | rationale | super.in, but typed as SimpleBufferedInput / logical cap ... | field units, sentinels, latch, allowClose reason |
| 33 | ambiguous | - | if we are tracking progress, will have the expected content l | mostly restates the field |
| 35-36 | keep | magic-number | expected content length for progress; -1 == unknown / amount | -1 sentinel |
| 48 | keep | api-contract | If this InputStream is not already a ControllableInputStream, | null input behaviour, 0 == infinite |
| 55 | fix (remove) | stale | bufferSize currently unused; consider implementing as a min s | no bufferSize param in this overload |
| 62 | fix | stale | If this InputStream is not already ... @param bufferSize the  | bufferSize is ignored, doc says it is used |
| 70 | keep | todo-with-reason | todo - bufferSize currently unused; consider implementing as | says what and why |
| 82 | remove | restates | emits a progress | call says it |
| 88 | keep | rationale | interrupted latches, because parse() may call twice | why the flag latches |
| 100 | ambiguous | - | don't read more than desired, even if available | near-restates `len = remaining` |
| 104 | ambiguous | - | loop trying to read until we get some data or hit the overall | explains retry loop, partly restates |
| 110 | remove | restates | completed | `read == -1` says it |
| 114 | ambiguous | - | track bytes returned to the caller | near-restates |
| 116 | keep | todo-with-reason | todo: use long progress values in the public API; saturate un | what and until when |
| 130 | keep | rationale | implemented here so our cap accounting aligns | why skip is overridden |
| 152 | keep | api-contract | Reads this inputstream to a ByteBuffer. The supplied max may b | public static method doc |
| 160 | ambiguous | - | Share the same byte[] pool as SBI | restates call, or rationale |
| 168 | ambiguous | - | needs to grow | restates the condition, small aid |
| 181 | remove | restates | Prepare the buffer for reading | restates flip() |
| 188, 205 | keep | rationale | not synchronized in later JDKs | reason for the suppression |
| 201 | ambiguous | - | readPos is used for progress emits | mild rationale |
| 211 | keep | api-contract | Check if the underlying InputStream has been read fully. Ther | public method doc |
| 224 | keep | api-contract | Get the max size of this stream (how far at most will be read | public method doc |
| 233 | remove | restates | update remaining to reflect the difference in the new maxsize | restates the line |
| 241 | keep | api-contract | Check if content remains beyond the configured cap. | public method doc |
| 257 | keep | api-contract | Returns whether content was found beyond the configured cap. | public method doc |
| 281 | remove | restates | calculate percent complete if contentLength > 0 (and cap to 1 | restates next line; names nonexistent `totalRead` |
| 284 | keep | rationale | detach once we reach 100%, so that any subsequent buffer hits | why progress is nulled |
| 305-306 | keep | trap | called via HttpConnection.Response.bodyStream(), needs an OG B | must wrap `this`, not `buff` |

## Ambiguous, not scored

- 33: restates the field's purpose, but a reasonable reader might keep it.
- 100, 114: short trailing comments close to restating; harmless.
- 104: describes the retry-on-SocketTimeout loop; partly restates, partly explains intent.
- 160: could be restates (call names the pool) or rationale (shared pool on purpose).
- 168: "needs to grow" is a tiny aid to the condition.
- 201: hints why readPos is restored; weak rationale.
