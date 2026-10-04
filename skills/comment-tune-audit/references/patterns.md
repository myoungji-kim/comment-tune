# Grep patterns

Cheap first-pass hints. A hit is a candidate, not a verdict: read the comment
before judging. Patterns are extended regex for `git grep -nIE` or `rg -n`,
one per line, prefixed with the tag they hint at. Comment markers covered:
`//`, `/*`, `*`, `///`, `#`.

## trim hints

```
narration   (//|#|\*)\s*(Added|Updated|Changed|Modified|Refactored|Replaced|Moved|Renamed|Fixed|Now uses|New:)\b
narration   (//|#|\*).*\b(as requested|as discussed|per (the )?(review|request|feedback|ticket)|this (fix|change|PR|commit))\b
history     (//|#|\*).*\b(previously|used to|no longer|the old (code|version|implementation)|instead of the old)\b
history     (//|#|\*).*\b(I|we)('ve| have| had)? (added|changed|decided|switched|moved|chose)\b
banner      ^\s*(//|#|/\*)\s*[-=*#~_]{4,}
bare-todo   \b(TODO|FIXME|XXX|HACK)\b:?\s*(\*/)?\s*$
bare-todo   \b(TODO|FIXME)\b:?\s*(fix|fix this|later|refactor|cleanup|clean up)\.?\s*$
dead-code   ^\s*(//|#)\s*(return|if \(|for \(|while \(|const |let |var |final |await |import )
dead-code   ^\s*//\s*[A-Za-z_][A-Za-z0-9_.]*\(.*\);\s*$
```

## fill hints

Code with no comment directly above it is a candidate.

```
workaround    \b(sleep|Thread\.sleep|setTimeout|Future\.delayed|delay)\(
workaround    catch\s*(\([^)]*\))?\s*\{\s*\}
magic-number  [=(,<>]\s*-?[0-9]{3,}[0-9_]*\b
trap          \b(synchronized|volatile|Mutex|unawaited|runZoned|@Transactional)\b
```

For `magic-number`, skip values that already have a named constant with an
obvious name, years, and ports in config files.

## Excludes

Generated and vendored paths, as `git grep` pathspecs:

```
':!*.g.dart' ':!*.freezed.dart' ':!*.pb.*' ':!*_pb2.py' ':!*.min.js'
':!**/node_modules/**' ':!**/build/**' ':!**/dist/**' ':!**/generated/**'
':!**/vendor/**' ':!*.lock'
```
