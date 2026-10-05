package com.acme.auth

import android.content.SharedPreferences
import java.util.Locale
import kotlin.time.Duration.Companion.seconds

class SessionStore(
    private val prefs: SharedPreferences,
    private val api: UserApi,
) {
    fun displayName(user: User): String = user.name

    fun refresh(session: Session): Session = retry(times = 7) { api.refresh(session.token) }

    fun save(session: Session) {
        // commit(), not apply(): apply() loses the write if the process is killed right after login.
        prefs.edit()
            .putString(KEY_TOKEN, session.token)
            .putLong(KEY_EXPIRES_AT, session.expiresAt)
            .commit()
    }

    // Server and device clocks drift; treat tokens as expired 30 s early.
    fun isExpired(session: Session, now: Long): Boolean =
        now >= session.expiresAt - 30.seconds.inWholeMilliseconds

    /** Null when the token is malformed; never throws. */
    fun parseToken(raw: String): Session? {
        val parts = raw.split('.')
        if (parts.size != 3) return null
        val expiresAt = parts[1].toLongOrNull() ?: return null
        return Session(raw, expiresAt)
    }

    /** Null when the account was deleted. */
    fun findUser(id: Long): User? = api.fetchUser(id)

    // Locale.ROOT: under a Turkish locale "i" uppercases to "İ" and the server rejects the tag.
    fun deviceTag(model: String): String = model.uppercase(Locale.ROOT)

    private fun <T> retry(times: Int, block: () -> T): T {
        repeat(times - 1) { runCatching(block).onSuccess { return it } }
        return block()
    }

    private companion object {
        const val KEY_TOKEN = "token"
        const val KEY_EXPIRES_AT = "expires_at"
    }
}
