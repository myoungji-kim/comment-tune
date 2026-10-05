# oss-kt-kotlin-result-iterable labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 3 | keep | api-contract | Returns `true` if each element [is ok][Result.isOk], `false` | public KDoc, matches code |
| 10 | keep | api-contract | Returns `true` if each element [is an error][Result.isErr],  | public KDoc, matches code |
| 17 | keep | api-contract | Returns `true` if at least one element [is ok][Result.isOk], | public KDoc, matches code |
| 24 | keep | api-contract | Returns `true` if at least one element [is an error][Result. | public KDoc, matches code |
| 31 | keep | api-contract | Returns the number of elements that [are ok][Result.isOk]. | public KDoc, matches code |
| 38 | keep | api-contract | Returns the number of elements that [are an error][Result.is | public KDoc, matches code |
| 45 | keep | api-contract | Returns a list containing only elements that [are ok][Result | public KDoc, matches code |
| 54 | keep | api-contract | Returns a list containing only elements that [are an error][ | public KDoc, matches code |
| 61 | keep | api-contract | Appends the [values][Result.value] of each element that [is  | public KDoc, matches code |
| 76 | keep | api-contract | Appends the [errors][Result.error] of each element that [is  | public KDoc, matches code |
| 91 | keep | api-contract | Performs the given [action] on each [ok][Result.isOk] value  | public KDoc, matches code |
| 102 | keep | api-contract | Performs the given [action] on each [error][Result.isErr] va | public KDoc, matches code |
| 113 | keep | api-contract | Performs the given [action] on each [ok][Result.isOk] value  | public KDoc, matches code |
| 126 | keep | api-contract | Performs the given [action] on each [error][Result.isErr] va | public KDoc, matches code |
| 139 | keep | api-contract | Partitions the specified [results] into a [Pair] of [Lists][ | public KDoc, matches code |
| 151 | keep | api-contract | Partitions [this] iterable into a [Pair] of [Lists][List]. A | public KDoc, matches code |
| 163 | keep | api-contract | Partitions [this] iterable into a [Pair] of collections. The | public KDoc, matches code |
| 187 | keep | api-contract | Combines the specified [results] into a single [Result] (hol | public KDoc, matches code |
| 203 | keep | api-contract | Combines [this] iterable into a single [Result] (holding a [ | public KDoc, matches code |
| 226 | keep | api-contract | Combines [this] iterable into a single [Result], appending a | public KDoc, matches code |
| 248 | keep | api-contract | Combines the specified [results] into a single [Result] (hol | public KDoc, matches code |
| 260 | keep | api-contract | Combines [this] iterable into a single [Result] (holding a [ | public KDoc, matches code |
| 279 | keep | api-contract | Combines [this] iterable into a single [Result], appending a | public KDoc, matches code |
| 301 | ambiguous | - | Returns a [List] containing the [value][Result.value] of eac | Haskell lefts/rights cross-ref may be swapped |
| 312 | ambiguous | - | Returns a [List] containing the [error][Result.error] of eac | Haskell lefts/rights cross-ref may be swapped |

Reference is identical to the input: every KDoc is public API documentation
that matches the code (all/any/count, filter, onEach, partition, combine,
combineErr semantics and ordering were checked against the bodies).

## Ambiguous, not scored

- line 301 (`valuesOf`) and line 312 (`errorsOf`): they point to Haskell
  `Data.Either.lefts` for ok values and `rights` for errors. By Haskell
  convention `Right` is success, so the links look swapped; by type-parameter
  position (`Result<V, E>` vs `Either a b`) they line up. Could be `stale`,
  could be intentional; not scored.
- Short one-liners like `countOk` ("Returns the number of elements that are ok")
  are near-restatements, but they are public KDoc a doc tool depends on, so
  scored as api-contract keeps rather than noise.
