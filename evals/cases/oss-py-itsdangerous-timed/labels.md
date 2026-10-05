# oss-py-itsdangerous-timed labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 23 | keep | api-contract | Works like the regular :class:`.Signer` but also records the | public class doc, raises |
| 30 | keep | api-contract | Returns the current timestamp. The function must return an | override contract |
| 36 | keep | api-contract | Convert the timestamp from :meth:`get_timestamp` into an awa | public doc, tz-aware UTC |
| 46 | ambiguous | - | Signs the given string and also attaches time information. | restates, but public autodoc |
| 53 | keep | workaround | # Ignore overlapping signatures check, return_timestamp is th | explains pyright ignore |
| 57 | keep | untouchable | # pyright: ignore | tooling directive |
| 78 | keep | api-contract | Works like the regular :meth:`.Signer.unsign` but can also v | public method doc |
| 97 | ambiguous | - | # If there is no timestamp in the result there is something | verbose, but explains error precedence |
| 117 | ambiguous | - | # Signature is *not* okay. Raise a proper error now that we | half restates, half why deferred |
| 124 | keep | constraint | # Windows raises OSError / # 32-bit raises OverflowError | platform quirks |
| 132 | ambiguous | - | # Signature was okay but the timestamp is actually not there | half restates, "should not happen" |
| 137 | remove | restates | # Check timestamp is not older than max_age | the `if age > max_age` says it |
| 161 | ambiguous | - | Only validates the given signed value. Returns ``True`` if | mostly in signature, but public autodoc |
| 171 | ambiguous | - | Uses :class:`TimestampSigner` instead of the default | restates default_signer, but public autodoc |
| 175 | keep | untouchable | # pyright: ignore | tooling directive |
| 182 | keep | todo-with-reason | # TODO: Signature is incompatible because parameters were ad | explains type: ignore[override] |
| 185 | keep | untouchable | # type: ignore[override] | tooling directive |
| 192 | keep | api-contract | Reverse of :meth:`dumps`, raises :exc:`.BadSignature` if the | public method doc, raises |
| 214 | keep | rationale | # The signature was unsigned successfully but was expired. Do | why not try next signer |
| 222 | keep | untouchable | # type: ignore[override] | tooling directive |

## Ambiguous, not scored

- 46, 161, 171: short public docstrings that restate the code; criteria conflict
  (restates vs untouchable autodoc).
- 97: five lines that could be one ("no timestamp: re-raise the signature
  error, else non-timestamp data"), so `verbose` fits, but it carries a real
  ordering point.
- 117, 132: each half restates the `if` and half explains why; neither clearly
  trim nor clearly keep.
- 192 (kept, not stale): "All arguments are forwarded to the signer's unsign
  method" is loose: `salt` goes to `iter_unsigners` and `return_timestamp` is
  always `True` in the call. Arguably stale; left out as upstream wording.
