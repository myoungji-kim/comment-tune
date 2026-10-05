# Examples

Read this only when a call is close. Each example shows the input and the
verdict.

## trim

```java
// Get the user by id
User user = userRepository.findById(id);
```
`remove` · `restates` — the call says it.

```ts
// Updated to use the new retry helper as requested in review
await withRetry(() => client.send(msg));
```
`remove` · `narration`. Nothing left for the code. Commit draft: "Use
withRetry for message sends."

```dart
// We used to fetch this on every build, which was slow, so I moved it to
// initState. Now it only runs once.
_future = repository.load();
```
`remove` · `history`. Commit draft: "Load data once in initState instead of
on every build."

```java
/**
 * This method calculates the total price of the order. It loops over all
 * the items in the order and adds up their prices, then applies the
 * discount. Note that the discount is applied after tax because the
 * accounting team requires it.
 */
```
`rewrite` · `verbose` →
`/** Discount is applied after tax (accounting requirement). */`

```kotlin
// Room runs this migration in a transaction, so the copy and the rename land
// together or not at all. SQLite before 3.25 can't rename columns, hence the
// copy instead of ALTER TABLE ... RENAME COLUMN. Keep the old table until the
// next release: v4.1 clients still read it.
```
`keep`. Long, but every sentence is a separate fact the code can't show.
Squeezing it to one line would drop at least one of them.

```ts
// const legacy = await fetchLegacy(id);
// if (legacy) return legacy;
```
`remove` · `dead-code`.

```dart
// ============== Helpers ==============
```
`remove` · `banner`.

```java
// TODO: fix this
```
`remove` · `bare-todo`. If you can see what is wrong, say so instead:
`// TODO: handle the empty-cart case (returns 0 today)`.

## keep

```java
// Stripe rejects descriptors over 22 chars, so truncate before sending.
String descriptor = name.substring(0, Math.min(22, name.length()));
```
keep — external constraint.

```ts
// Must run before initAuth(): auth reads the region from this config.
loadConfig();
```
keep — `trap`.

```dart
// ignore: use_build_context_synchronously
Navigator.of(context).pop();
```
keep — untouchable directive.

## fill

```java
Thread.sleep(250);
```
`git log -L` on the line says "Throttle Stripe calls: their API allows 4
requests per second per account". `add` · `magic-number` →
`// Stripe allows 4 req/s per account; 250 ms keeps us under it.`

```ts
if (items.length > 500) return chunk(items, 500).flatMap(send);
```
No evidence anywhere for 500. `add (needs input)` · `magic-number` → ask:
"Where does the 500-item limit come from?"

## fix

```java
// Returns null if the user is not found.
public Optional<User> find(long id) {
```
`rewrite` · `stale` → `// Empty if the user is not found.` (or `remove`,
since `Optional` already says it).

```ts
// Retries 3 times
const MAX_RETRIES = 5;
```
`remove` · `stale` + `restates` — the true version restates the constant.

## commit message draft

Collect the useful parts of removed `history` and `narration` comments:

```
Load data once in initState instead of on every build
Use withRetry for message sends
```

Skip lines that only said "added" or "updated" with no reason.
