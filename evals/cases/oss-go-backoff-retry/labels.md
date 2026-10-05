# oss-go-backoff-retry labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 9 | keep | api-contract | DefaultMaxElapsedTime sets a default limit for the total... | exported godoc |
| 12 | keep | api-contract | Operation is the function Retry calls. It is invoked at... | exported godoc, Permanent/RetryAfter contract |
| 17 | keep | api-contract | Notify is called after a failed attempt that will be ret... | exported godoc, when it fires |
| 23 | remove | restates | retryOptions holds configuration settings for the retry... | non-public doc that only restates the name |
| 25 | fix | stale | Strategy for calculating backoff periods. / Timer ... / Maximum number of retry attempts. | MaxTries counts attempts, not retries |
| 32 | keep | api-contract | RetryOption configures the behavior of Retry. | exported godoc |
| 35 | keep | api-contract | WithBackOff configures the backoff policy used between... | exported godoc, concurrency note |
| 47 | remove | restates | withTimer sets a custom timer for managing delays betwe... | non-public doc that only restates the name |
| 54 | keep | api-contract | WithNotify sets a function called after each failed att... | exported godoc |
| 62 | keep | api-contract | WithMaxTries limits the total number of attempts, not r... | exported godoc, attempts vs retries |
| 71 | keep | api-contract | WithMaxElapsedTime limits the total wall-clock time spe... | exported godoc, long but a real contract |
| 100 | keep | api-contract | Retry attempts the operation until it succeeds, returns... | exported godoc, errors and ctx |
| 115 | remove | restates | Initialize default retry options. | code says it |
| 122 | remove | restates | Apply user-provided options to the default settings. | code says it |
| 132 | remove | restates | Execute the operation. | code says it |
| 138 | remove | restates | Stop immediately on a permanent error; surface it as a R... | code says it |
| 144 | keep | trap | A RetryAfterError carries the delay before the next att... | unwrap choice, typed-nil trap |
| 155 | remove | restates | Stop retrying if maximum tries exceeded. | code says it |
| 160 | remove | restates | Stop retrying if context is cancelled. | code says it |
| 165 | remove | restates | Calculate next backoff duration. | code says it |
| 171 | remove | restates | Reset backoff if a RetryAfterError requested a specific... | code says it |
| 177 | keep | rationale | A negative delay (e.g. a Retry-After date already in th... | why the clamp exists |
| 183 | remove | restates | Stop retrying if maximum elapsed time exceeded. | restates the check, and loosely: it stops when the next wait would overrun |
| 188 | remove | restates | Notify on error if a notifier function is provided. | code says it |
| 193 | remove | restates | Wait for the next backoff period or context cancellation. | code says it |

Lines 25-29 are trailing field comments on consecutive lines, so the scorer
merges them into one comment; only the MaxTries part is wrong.

## Ambiguous, not scored

- None.
