# oss-dart-http-retry labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 1 | keep | untouchable | Copyright (c) 2017, the Dart project authors. | license header |
| 12 | keep | api-contract | An HTTP client wrapper that automatically retries failing... | public class doc, memory cost note |
| 18 | remove | restates | The wrapped client. | non-public doc that only restates the name |
| 21 | remove | restates | The number of times a request should be retried. | non-public doc that only restates the name |
| 24 | ambiguous | - | The callback that determines whether a request should be... | private field doc |
| 27 | ambiguous | - | The callback that determines whether a request when an er... | private field, garbled grammar |
| 30 | ambiguous | - | The callback that determines how long to wait before retr... | private field doc |
| 33 | ambiguous | - | The callback to call to indicate that a request is being ... | private field doc |
| 36 | keep | api-contract | Creates a client wrapping [_inner] that retries HTTP requ... | public constructor contract; defaults match code |
| 76 | keep | api-contract | Like [RetryClient.new], but with a pre-computed list of [... | public constructor contract |
| 125 | keep | rationale | If the inner client doesn't support abortable, we still t... | why the manual abort check |
| 139 | keep | workaround | Make sure the response stream is listened to so that we d... | explains listen().cancel() |
| 150 | remove | restates | Returns a copy of [original] with the given [body]. | non-public doc that only restates the name |

## Ambiguous, not scored

- 24, 30, 33: dartdoc on private fields whose names don't say enough on their own (`_when`, `_delay`); not pure restates.
- 27: "whether a request when an error is thrown" is missing words; a rewrite is reasonable, but it is not stale.
