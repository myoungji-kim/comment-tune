# oss-go-backoff-exponential labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 9 | keep | api-contract | ExponentialBackOff is a backoff implementation that incr... | exported godoc, formula and defaults table |
| 57 | keep | api-contract | Default values for ExponentialBackOff. | exported const group godoc |
| 65 | keep | api-contract | NewExponentialBackOff creates an instance of Exponential... | exported godoc |
| 75 | fix | stale | Reset the interval back to the initial retry interval and restarts the timer. | there is no timer |
| 75 | fix | stale | Reset must be called before using b. | NextBackOff initializes a zero interval itself |
| 81 | keep | api-contract | NextBackOff calculates the next backoff interval using t... | exported godoc |
| 94 | remove | restates | Increments the current interval by multiplying it with... | non-public doc that only restates the name |
| 96 | ambiguous | - | Check for overflow, if overflow is detected set the cur... | half restates, half why the division |
| 104 | remove | restates | Returns a random value from the following interval: | non-public doc that only restates the name |
| 109 | remove | restates | make sure no randomness is used when randomizationFactor... | the early return says it |
| 115 | keep | magic-number | Get a random value from the range [minInterval, maxInter... | explains the +1 |
| 119 | keep | trap | float64(math.MaxInt64) rounds up to 2^63, which does not... | float overflow trap |

Lines 75-76 are one merged comment carrying two stale claims; the reference
rewrites it to `Reset sets the interval back to the initial retry interval.`

## Ambiguous, not scored

- 96 `Check for overflow...`: the condition is written as a division to avoid
  overflow, which is worth saying, but the comment mostly restates the branch.
- Line 9 block also uses `RetryInterval`, which is not a field name
  (`InitialInterval`/`currentInterval`); a conceptual name upstream, not
  labelled stale. Only its thread-safety note is scored.
