# oss-ts-ky-constants labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 15 | keep | untouchable | @ts-expect-error - Types are outdated. | compiler directive |
| 22 | keep | constraint | Unsupported implementations throw different errors, such as | platform quirk, issue #581 |
| 48-49 | keep | constraint | Supported in modern Fetch implementations (for example, brow | runtime support caveat; feature check exists in body.ts |
| 53 | keep | magic-number | The maximum value of a 32bit int (see issue #117) | source of 2_147_483_647 |
| 56 | keep | magic-number | Size in bytes of a typical form boundary (e.g., '------WebK | source of 40 |
| 59-61 | keep | api-contract | Symbol that can be returned by a `beforeRetry` hook to stop | public API doc |
| 64-66 | keep | api-contract | Options for forcing a retry via `ky.retry()`. | public type doc |
| 68-74 | keep | api-contract | Custom delay in milliseconds before retrying. | public option doc (units, jitter bypass) |
| 77-87 | keep | api-contract | Error code for the retry. | public option doc |
| 90-107 | keep | api-contract | Original error that caused the retry. | public option doc |
| 110-142 | keep | api-contract | Custom request to use for the retry. | public option doc, security warning |
| 146-148 | keep | api-contract | Marker returned by `ky.retry()` to signal a forced retry fro | public class doc |
| 157-239 | keep | api-contract | Force a retry from an `afterResponse` hook. | public function doc with example |
| 261-265 | keep | constraint | Standard RequestInit options that should NOT be passed separ | why dispatcher/priority are absent; matches the list |

## Ambiguous, not scored

None.
