# oss-kt-cronet-callback-proxy labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 1 | keep | untouchable | Copyright (c) 2023, the Dart project authors. Please see | license header |
| 5 | keep | constraint | Cronet allows developers to manage HTTP requests by subclass | jnigen can't subclass abstract Java classes (issue 348); explains why the proxy exists |
| 23 | keep | workaround | Due to a bug (https://github.com/dart-lang/native/issues/242 | all params nullable on purpose to dodge a JNIgen bug; real nullability documented |

Reference is identical to the input: nothing to trim or fix.

## Ambiguous, not scored

None. Both long comments could be argued `verbose`, but each line carries a
fact (issue link, why nullable, which param is really nullable) and the 11-line
length fits the "trap that needs the whole story" exception, so they are kept.
