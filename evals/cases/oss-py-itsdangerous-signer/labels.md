# oss-py-itsdangerous-signer labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 16 | keep | api-contract | Subclasses must implement :meth:`get_signature` to provide | subclass contract |
| 21 | keep | api-contract | Returns the signature for the given key and value. | public doc, kept even when it restates the name |
| 25 | keep | api-contract | Verifies the given signature matches the expected signature. | public doc, kept even when it restates the name |
| 32 | keep | api-contract | Provides an algorithm that does not perform any signing and | public doc, kept even when it restates the name |
| 41 | keep | constraint | Don't access ``hashlib.sha1`` until runtime. FIPS builds may | FIPS builds lack SHA-1 |
| 49 | keep | api-contract | Provides signature generation using HMACs. | public doc, kept even when it restates the name |
| 51 | keep | api-contract | #: The digest method to use with the MAC algorithm. This def | Sphinx attribute doc |
| 73 | keep | untouchable | # pyright: ignore | tooling directive |
| 77 | keep | api-contract | A signer securely signs bytes, then unsigns them to verify | public class doc |
| 114 | keep | api-contract | #: The default digest method to use for the signer. The defa | Sphinx attribute doc |
| 122 | keep | api-contract | #: The default scheme to use to derive the signing key from t | Sphinx attribute doc |
| 138 | keep | api-contract | #: The list of secret keys to try for verifying signatures, f | Sphinx attribute doc, key order |
| 177 | keep | api-contract | The newest (last) entry in the :attr:`secret_keys` list. This | public property, compat reason |
| 183 | keep | api-contract | This method is called to derive the key. The default key der | override point, security note |
| 216 | keep | api-contract | Returns the signature for the given value. | public doc, kept even when it restates the name |
| 223 | keep | api-contract | Signs the given string. | public doc, kept even when it restates the name |
| 228 | keep | api-contract | Verifies the signature for the given value. | public doc, kept even when it restates the name |
| 245 | keep | api-contract | Unsigns the given string. | public doc, kept even when it restates the name |
| 259 | keep | api-contract | Only validates the given signed value. Returns ``True`` if | public doc, kept even when it restates the name |

## Ambiguous, not scored

- 77, 122 (kept, not stale): the documented `key_derivation` values list
  `concat`, `django-concat`, `hmac`, but `derive_key` also accepts `none`. Could
  be an intentionally undocumented value, so not labeled stale.
