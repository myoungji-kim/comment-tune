# oss-ts-ky-body labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 8 | keep | untouchable | eslint-disable-next-line @typescript-eslint/no-restricted-t | linter directive |
| 15 | keep | rationale | This is an approximation, as FormData size calculation is n | result is deliberately approximate |
| 60 | keep | rationale | Avoid reporting 100% progress before the stream is actually | why percent is capped |
| 62-63 | keep | rationale | Epsilon is used here to get as close as possible to 100% wi | rejected 0.99 alternative |
| 85-86 | keep | workaround | Chromium replaces stream errors with a generic TypeError in | browser quirk behind the method wrapping |
| 108 | keep | constraint | The `Response` constructor cannot set these, so copy them o | platform limit |
| 112-113 | keep | rationale | Native `clone()` creates a new `Response`, which would drop | why clone is shimmed, writable/configurable |
| 117 | keep | trap | Cloning replaces the original body too, so retain the error | non-obvious side effect of clone |
| 166 | keep | untouchable | eslint-disable-next-line @typescript-eslint/no-restricted-t | linter directive; same text as line 8, one case.json item covers both |
| 172 | keep | rationale | Use original body for size calculation since request.body i | why originalBody is preferred |
| 176 | keep | untouchable | @ts-expect-error - Types are outdated. | compiler directive |

## Ambiguous, not scored

None.
