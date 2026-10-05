# oss-py-itsdangerous-timed labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 23 | keep | api-contract | Works like the regular :class:`.Signer` but also records the | public class doc, raises |
| 30 | keep | api-contract | Returns the current timestamp. The function must return an | override contract |
| 36 | keep | api-contract | Convert the timestamp from :meth:`get_timestamp` into an awa | public doc, tz-aware UTC |
| 46 | keep | api-contract | Signs the given string and also attaches time information. | public doc, kept even when it restates the name |
| 53 | keep | workaround | # Ignore overlapping signatures check, return_timestamp is th | explains pyright ignore |
| 57 | keep | untouchable | # pyright: ignore | tooling directive |
| 78 | keep | api-contract | Works like the regular :meth:`.Signer.unsign` but can also v | public method doc |
| 97 | rewrite | verbose | # If there is no timestamp in the result there is something | one point: a signature error wins over a missing timestamp |
| 117 | ambiguous | - | # Signature is *not* okay. Raise a proper error now that we | half restates, half why deferred |
| 124 | keep | constraint | # Windows raises OSError / # 32-bit raises OverflowError | platform quirks |
| 132 | ambiguous | - | # Signature was okay but the timestamp is actually not there | half restates, "should not happen" |
| 137 | remove | restates | # Check timestamp is not older than max_age | the `if age > max_age` says it |
| 161 | keep | api-contract | Only validates the given signed value. Returns ``True`` if | public doc, kept even when it restates the name |
| 171 | keep | api-contract | Uses :class:`TimestampSigner` instead of the default | public doc, kept even when it restates the name |
| 175 | keep | untouchable | # pyright: ignore | tooling directive |
| 182 | keep | todo-with-reason | # TODO: Signature is incompatible because parameters were ad | explains type: ignore[override] |
| 185 | keep | untouchable | # type: ignore[override] | tooling directive |
| 192 | fix | stale | Reverse of :meth:`dumps`, raises :exc:`.BadSignature` if the | not all arguments are forwarded: salt picks signers, return_timestamp is fixed |
| 214 | keep | rationale | # The signature was unsigned successfully but was expired. Do | why not try next signer |
| 222 | keep | untouchable | # type: ignore[override] | tooling directive |

## Ambiguous, not scored

- 117, 132: each half restates the `if` and half explains why; neither clearly
  trim nor clearly keep.
