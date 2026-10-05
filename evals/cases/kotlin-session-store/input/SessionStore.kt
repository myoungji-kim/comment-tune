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
        prefs.edit()
            .putString(KEY_TOKEN, session.token)
            .putLong(KEY_EXPIRES_AT, session.expiresAt)
            .commit()
    }

    // So basically what happens here is that the token we get back from the
    // auth server can sometimes be expired already by the time we use it,
    // because the server clock and the device clock aren't always in sync,
    // so we subtract a bit just to be on the safe side.
    fun isExpired(session: Session, now: Long): Boolean =
        now >= session.expiresAt - 30.seconds.inWholeMilliseconds

    /** Null when the token is malformed; never throws. */
    fun parseToken(raw: String): Session? {
        val parts = raw.split('.')
        if (parts.size != 3) return null
        val expiresAt = parts[1].toLongOrNull() ?: return null
        return Session(raw, expiresAt)
    }

    fun findUser(id: Long): User? = api.fetchUser(id)

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
