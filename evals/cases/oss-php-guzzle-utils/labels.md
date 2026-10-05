# oss-php-guzzle-utils labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 25 | keep | api-contract | Parses an array of header lines into an associative arra... | public doc, line format |
| 43 | keep | api-contract | Returns a debug stream based on the provided variable. | public doc, @return resource |
| 62 | keep | api-contract | Chooses and creates a default handler to use based on th... | public doc, no middlewares, throws |
| 86 | keep | constraint | libcurl below 8.22.0 does not apply cURL multi connectio... | upstream curl bug, downgrade reason |
| 95 | keep | constraint | Handler-scoped required sharing can also be satisfied by... | PHP 8.6+ / cURL-only sharing |
| 130 | keep | untouchable | @param array{max_host_connections?: mixed, max_total_con... | type info; not scored, see below |
| 138 | keep | untouchable | @param array{...multiplex?: mixed} / @return (callable(... | type info |
| 150 | keep | rationale | Required handler sharing can also be satisfied by the st... | why null instead of failing |
| 164 | keep | constraint | Forwarded to the CurlMultiHandler only: CurlHandler and... | other handlers reject the option |
| 174 | keep | trap | Connection caps only govern transfers on the multi handl... | why no sync fast path |
| 193 | keep | untouchable | @return array<string, mixed> | type info |
| 207 | keep | untouchable | @param array{...} / @return array{max_host_connections?:... | type info |
| 231 | keep | untouchable | @param (callable(RequestInterface, ... $handler | type info |
| 246 | ambiguous | - | Get the default User-Agent string to use with Guzzle. | see below |
| 254 | keep | api-contract | Creates an associative array of lowercase header names t... | public doc, key/value direction |
| 268 | keep | untouchable | @param mixed $protocols / @return string[] / @throws Inv... | type info |

No noise and nothing stale: every comment is either type info, a public
contract, or a reason the code cannot show.

## Ambiguous, not scored

- 246 `Get the default User-Agent string to use with Guzzle.`: restates the
  method name (criteria `restates` example), yet it is public PHPDoc that API
  docs render.
- 130: untouchable type info, but its whole text also appears inside the 207
  doc, so no substring names it uniquely; left out of case.json.
