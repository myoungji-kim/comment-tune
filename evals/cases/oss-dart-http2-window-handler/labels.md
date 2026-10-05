# oss-dart-http2-window-handler labels

| line | verdict | tag | comment | why |
|---|---|---|---|---|
| 1 | keep | untouchable | Copyright (c) 2015, the Dart project authors. | license header |
| 12 | fix | stale | The connection flow control window. | also a stream window via OutgoingStreamWindowHandler |
| 15 | fix | stale | Indicates when the outgoing connection window turned posi... | same: base class serves stream windows too |
| 25 | keep | api-contract | The flow control window size we use for sending data. We ... | public getter, must-not-go-negative rule |
| 29 | keep | api-contract | Process a window update frame received from the remote end. | public method doc |
| 41 | ambiguous | - | If we transitioned from an negative/empty window to a pos... | explains the condition below |
| 48 | keep | api-contract | Update the peer window by subtracting [numberOfBytes]. | public method, who restores the window |
| 60 | keep | api-contract | Handles the connection window for outgoing data frames. | public class doc |
| 65 | keep | api-contract | Handles the window for outgoing messages to the peer. | public class doc |
| 69 | keep | api-contract | Update the peer window by adding [difference] to it. | public method, SETTINGS trigger |
| 92 | keep | api-contract | Mirrors the flow control window the remote end is using. | public class doc |
| 94 | ambiguous | - | The [FrameWriter] used for writing [WindowUpdateFrame]s t... | private field, near-restates |
| 97 | ambiguous | - | The mirror of the [Window] the remote end sees. | private field, meaning of negative |
| 103 | keep | magic-number | The stream id this window handler is for (is `0` for conn... | where stream id 0 comes from |
| 115 | keep | api-contract | The current size for the incoming data window. | public getter, never-negative invariant |
| 121 | keep | api-contract | Signals that we received [numberOfBytes] from the remote ... | public method doc |
| 125 | ambiguous | - | If this turns negative, it means the remote end send us m... | 22-line trap explanation |
| 154 | keep | todo-with-reason | Tell the peer we received [numberOfBytes] bytes. ... TODO... | public doc merged with TODO that names the pause case |
| 163 | keep | todo-with-reason | TODO: This can be optimized by delaying the window update... | TODO says what and why |

Reference fixes: line 12 becomes "The peer's flow control window (connection or stream level)."; line 15 drops "connection".

## Ambiguous, not scored

- 41: mostly restates the `if`, but names the event being fired; could go either way.
- 94: private field doc that mostly restates the type.
- 97: private field, but the "negative means the peer overran us" note is useful; no tag fits a private field cleanly.
- 125: true trap explanation (why case c can't happen), but 22 lines long; `verbose` rewrite or keep-as-is are both defensible, and the claim about initial settings can't be verified in this file.
