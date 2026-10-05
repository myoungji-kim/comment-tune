# oss-py-itsdangerous-signer labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 16 | keep | api-contract | Subclasses must implement :meth:`get_signature` to provide | subclass contract |
| 21 | ambiguous | - | Returns the signature for the given key and value. | restates, but public autodoc |
| 25 | ambiguous | - | Verifies the given signature matches the expected signature. | restates, but public autodoc |
| 32 | ambiguous | - | Provides an algorithm that does not perform any signing and | restates, but public autodoc |
| 41 | keep | constraint | Don't access ``hashlib.sha1`` until runtime. FIPS builds may | FIPS builds lack SHA-1 |
| 49 | ambiguous | - | Provides signature generation using HMACs. | restates class name, but public autodoc |
| 51 | keep | api-contract | #: The digest method to use with the MAC algorithm. This def | Sphinx attribute doc |
| 73 | keep | untouchable | # pyright: ignore | tooling directive |
| 77 | keep | api-contract | A signer securely signs bytes, then unsigns them to verify | public class doc |
| 114 | keep | api-contract | #: The default digest method to use for the signer. The defa | Sphinx attribute doc |
| 122 | keep | api-contract | #: The default scheme to use to derive the signing key from t | Sphinx attribute doc |
| 138 | keep | api-contract | #: The list of secret keys to try for verifying signatures, f | Sphinx attribute doc, key order |
| 177 | keep | api-contract | The newest (last) entry in the :attr:`secret_keys` list. This | public property, compat reason |
| 183 | keep | api-contract | This method is called to derive the key. The default key der | override point, security note |
| 216 | ambiguous | - | Returns the signature for the given value. | restates, but public autodoc |
| 223 | ambiguous | - | Signs the given string. | restates, but public autodoc |
| 228 | ambiguous | - | Verifies the signature for the given value. | restates, but public autodoc |
| 245 | ambiguous | - | Unsigns the given string. | restates, but public autodoc |
| 259 | ambiguous | - | Only validates the given signed value. Returns ``True`` if | mostly in signature, but public autodoc |

## Ambiguous, not scored

- 21, 25, 32, 49, 216, 223, 228, 245, 259: one-line public docstrings that restate
  the method name. Criteria call `/** Gets the user. */` restates, but also make
  doc comments that Sphinx autodoc depends on untouchable.
- 77, 122 (kept, not stale): the documented `key_derivation` values list
  `concat`, `django-concat`, `hmac`, but `derive_key` also accepts `none`. Could
  be an intentionally undocumented value, so not labeled stale.
