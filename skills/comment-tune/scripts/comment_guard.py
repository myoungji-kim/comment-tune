#!/usr/bin/env python3
"""Prove that an edit changed comments only.

    comment_guard.py snapshot FILE...   record the comment-free code of FILEs
    comment_guard.py verify             report snapshotted files whose code changed
    comment_guard.py compare OLD NEW    compare two files directly
    comment_guard.py comments FILE      print the comments of FILE as JSON

Exit status: 0 when no code changed, 1 when some did, 2 on usage errors or
when a file can't be checked. A file using syntax the lexer doesn't model
(see UNMODELED) is reported as `unchecked (reason)` and left out of the
snapshot; check its diff by hand.
Whitespace is ignored, so re-indenting or reflowing around a comment is fine.
Standard library only, so the skill runs anywhere python3 does.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize

C_LIKE = {
    # extension: string delimiters the lexer must skip over
    ".java": ('"""', '"', "'"),
    ".kt": ('"""', '"', "'"),
    ".kts": ('"""', '"', "'"),
    ".scala": ('"""', '"', "'"),
    ".groovy": ("'''", '"""', '"', "'"),
    ".gradle": ("'''", '"""', '"', "'"),
    ".dart": ("'''", '"""', '"', "'"),
    ".js": ('"', "'", "`"),
    ".jsx": ('"', "'", "`"),
    ".mjs": ('"', "'", "`"),
    ".cjs": ('"', "'", "`"),
    ".ts": ('"', "'", "`"),
    ".tsx": ('"', "'", "`"),
    ".mts": ('"', "'", "`"),
    ".cts": ('"', "'", "`"),
    ".go": ('"', "'", "`"),
    ".c": ('"', "'"),
    ".h": ('"', "'"),
    ".cc": ('"', "'"),
    ".cpp": ('"', "'"),
    ".hpp": ('"', "'"),
    ".m": ('"', "'"),
    ".mm": ('"', "'"),
    ".cs": ('"', "'"),
    ".swift": ('"""', '"'),
    ".rs": ('"',),  # ' is also a lifetime marker in Rust
    ".css": ('"', "'"),
    ".scss": ('"', "'"),
    ".less": ('"', "'"),
}
HASH = {
    ".sh": ('"', "'"),
    ".bash": ('"', "'"),
    ".zsh": ('"', "'"),
    ".rb": ('"', "'"),
    ".yml": ('"', "'"),
    ".yaml": ('"', "'"),
    ".toml": ('"""', "'''", '"', "'"),
    ".properties": (),
    ".r": ('"', "'"),
    ".pl": ('"', "'"),
}
SUPPORTED = set(C_LIKE) | set(HASH) | {".py", ".php"}

JS_LIKE = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
# A regex literal starts where a value is expected: after an operator, an
# opening bracket, or `return`. Division can't follow those, so this is not
# fooled by `a / b / c`.
_JS_REGEX = (r"(?:^|[=(,:!&|?{};\[]|\breturn)\s*/(?![/*\s])"
             r"((?:\\.|\[(?:\\.|[^\]\n])*\]|[^/\\\n\[])+)/[a-z]*")
# Syntax the generic lexer doesn't model. A file that uses any of it gets no
# fingerprint: a wrong "ok" is worse than an honest "can't check".
UNMODELED = {
    **{ext: [("regex literal with a comment marker or quote",
              lambda s: any(re.search(r"//|/\*|['\"`]", s[m.start(1) - 1:m.end()])
                            for m in re.finditer(_JS_REGEX, s, re.M))),
             ("backtick inside a template ${...}", r"\$\{[^}`\n]*`")] for ext in JS_LIKE},
    ".rs": [("raw string", r"\br#*\""), ("'\"' char literal", r"'\"'")],
    ".cs": [("verbatim or raw string", r"@\"|\"\"\""),
            ("quote inside an interpolation hole", r"\$@?\"[^\"\n]*\{[^}\n]*\"")],
    ".swift": [("raw string", r"#+\"")],
    ".dart": [("raw string", r"\br['\"]")],
    ".c": [("raw string", r"\bR\"[^(\s]*\(")],
    ".cc": [("raw string", r"\bR\"[^(\s]*\(")],
    ".cpp": [("raw string", r"\bR\"[^(\s]*\(")],
    ".h": [("raw string", r"\bR\"[^(\s]*\(")],
    ".hpp": [("raw string", r"\bR\"[^(\s]*\(")],
    ".groovy": [("dollar-slashy string", r"\$/")],
    ".gradle": [("dollar-slashy string", r"\$/")],
    ".scss": [("unquoted url with //", r"url\(\s*[^'\")\s]*//")],
    ".less": [("unquoted url with //", r"url\(\s*[^'\")\s]*//")],
    ".rb": [("heredoc", r"<<[~-]?['\"]?[A-Za-z_]"), ("=begin block", r"^=begin"),
            ("percent literal", r"%[qQwWiIrsx]?[{(\[<|!/]")],
    ".sh": [("heredoc", r"<<-?\s*['\"]?\w")],
    ".bash": [("heredoc", r"<<-?\s*['\"]?\w")],
    ".zsh": [("heredoc", r"<<-?\s*['\"]?\w")],
    ".pl": [("heredoc", r"<<~?['\"]?\w"), ("POD block", r"^=\w")],
    ".yml": [("block scalar", r":\s*[|>][-+0-9]*\s*(#.*)?$")],
    ".yaml": [("block scalar", r":\s*[|>][-+0-9]*\s*(#.*)?$")],
    ".r": [("raw string", r"\b[rR]['\"]-*[(\[{]")],
}
NESTED_BLOCK_COMMENTS = {".rs", ".swift", ".kt", ".kts", ".scala", ".dart"}


def _skip_string(src, i, delims):
    """If a string literal starts at i, return the index just past it."""
    for d in delims:
        if src.startswith(d, i):
            j = i + len(d)
            while j < len(src):
                if src[j] == "\\" and len(d) == 1:
                    j += 2
                    continue
                if src.startswith(d, j):
                    return j + len(d)
                if src[j] == "\n" and d in ('"', "'"):
                    return j  # unterminated: don't swallow the file
                j += 1
            return j
    return None


def _lex(src, delims, line_marker, block):
    code, comments = [], []
    i, n = 0, len(src)
    while i < n:
        end = _skip_string(src, i, delims)
        if end is not None:
            code.append(src[i:end])
            i = end
            continue
        if line_marker and src.startswith(line_marker, i) and _hash_starts_comment(src, i, line_marker):
            j = src.find("\n", i)
            j = n if j < 0 else j
            comments.append((src.count("\n", 0, i) + 1, src[i:j]))
            code.append(" ")
            i = j
            continue
        if block and src.startswith(block[0], i):
            j = src.find(block[1], i + len(block[0]))
            j = n if j < 0 else j + len(block[1])
            comments.append((src.count("\n", 0, i) + 1, src[i:j]))
            code.append(" " + "\n" * src.count("\n", i, j))
            i = j
            continue
        code.append(src[i])
        i += 1
    return "".join(code), comments


def _hash_starts_comment(src, i, marker):
    if marker != "#":
        return True
    # `$#`, `${#x}` and `a#b` are not comments in shell-like languages.
    return i == 0 or src[i - 1] in " \t\n;("


def _lex_python(src):
    code, comments = [], []
    tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    prev = tokenize.NEWLINE
    for k, tok in enumerate(tokens):
        nxt = tokens[k + 1].type if k + 1 < len(tokens) else tokenize.ENDMARKER
        if tok.type == tokenize.COMMENT:
            comments.append((tok.start[0], tok.string))
        elif (tok.type == tokenize.STRING
              and prev in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT)
              and nxt in (tokenize.NEWLINE, tokenize.ENDMARKER)):
            comments.append((tok.start[0], tok.string))  # docstring
        elif tok.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                              tokenize.DEDENT, tokenize.ENDMARKER):
            code.append(tok.string)
        if tok.type not in (tokenize.COMMENT, tokenize.NL):
            prev = tok.type
    return " ".join(code), comments


_PHP_OPEN = re.compile(r"<\?(?:php\b|=|(?=\s))")
_PHP_HEREDOC = re.compile(r"<<<[ \t]*(['\"]?)([A-Za-z_]\w*)\1\r?\n")
_PHP_STRING = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`", re.S)


def _lex_php(src):
    """PHP: inline HTML outside <?php ... ?> is code, # and // end at ?>, strings span lines."""
    code, comments = [], []
    i, n, html = 0, len(src), True
    while i < n:
        if html:
            m = _PHP_OPEN.search(src, i)
            j = n if m is None else m.end()
            code.append(src[i:j])
            i, html = j, False
            continue
        if src.startswith("?>", i):
            code.append("?>")
            i, html = i + 2, True
            continue
        m = _PHP_HEREDOC.match(src, i)
        if m:
            # The closing marker may be indented (PHP 7.3+) and followed by `;`, `,` or `)`.
            end = re.compile(r"^[ \t]*" + re.escape(m[2]) + r"\b", re.M).search(src, m.end())
            j = n if end is None else end.end()
            code.append(src[i:j])
            i = j
            continue
        m = _PHP_STRING.match(src, i)
        if m:
            code.append(m[0])
            i = m.end()
            continue
        if src.startswith("//", i) or (src[i] == "#" and not src.startswith("#[", i)):
            j = i
            while j < n and src[j] != "\n" and not src.startswith("?>", j):
                j += 1
            comments.append((src.count("\n", 0, i) + 1, src[i:j]))
            code.append(" ")
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            comments.append((src.count("\n", 0, i) + 1, src[i:j]))
            code.append(" " + "\n" * src.count("\n", i, j))
            i = j
            continue
        code.append(src[i])
        i += 1
    return "".join(code), comments


def unchecked_reason(path, src=None):
    """Why this file's code can't be fingerprinted reliably, or None when it can."""
    if src is None:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED:
        return "unsupported type"
    if ext == ".py":
        try:
            _lex_python(src)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            return "Python that tokenize can't read"
        return None
    for name, test in UNMODELED.get(ext, []):
        if test(src) if callable(test) else re.search(test, src, re.M):
            return name
    if ext in NESTED_BLOCK_COMMENTS:
        if any(t.startswith("/*") and "/*" in t[2:] for _, t in split(path, src)[1]):
            return "nested block comment"
    return None


def split(path, src=None):
    """Return (code_without_comments, [(line, comment_text), ...])."""
    if src is None:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    ext = os.path.splitext(path)[1].lower()
    if ext == ".py":
        try:
            return _lex_python(src)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            return _lex(src, ('"""', "'''", '"', "'"), "#", None)
    if ext == ".php":
        return _lex_php(src)
    if ext in C_LIKE:
        # Plain CSS has no line comments: `//` there is usually part of a URL.
        return _lex(src, C_LIKE[ext], None if ext == ".css" else "//", ("/*", "*/"))
    if ext in HASH:
        return _lex(src, HASH[ext], "#", None)
    raise ValueError(f"unsupported file type: {path}")


def fingerprint(path, src=None):
    code, _ = split(path, src)
    return hashlib.sha256(" ".join(code.split()).encode()).hexdigest()


def _state_path():
    try:
        git_dir = subprocess.run(["git", "rev-parse", "--absolute-git-dir"],
                                 capture_output=True, text=True, check=True).stdout.strip()
        return os.path.join(git_dir, "comment-tune-snapshot.json")
    except (OSError, subprocess.CalledProcessError):
        key = hashlib.sha256(os.getcwd().encode()).hexdigest()[:12]
        return os.path.join(tempfile.gettempdir(), f"comment-tune-{key}.json")


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    cmd, args = argv[0], argv[1:]

    if cmd == "snapshot":
        state, skipped = {}, []
        for p in args:
            reason = unchecked_reason(p)
            if reason:
                skipped.append((p, reason))
            else:
                state[os.path.abspath(p)] = fingerprint(p)
        with open(_state_path(), "w") as f:
            json.dump(state, f)
        print(f"snapshot: {len(state)} file(s)")
        for p, reason in skipped:
            print(f"unchecked ({reason}): {p}")
        return 0

    if cmd == "verify":
        try:
            with open(_state_path()) as f:
                state = json.load(f)
        except FileNotFoundError:
            print("no snapshot: run `snapshot FILE...` before editing")
            return 2
        changed = [p for p, h in state.items()
                   if not os.path.exists(p) or fingerprint(p) != h]
        for p in changed:
            print(f"CODE CHANGED: {os.path.relpath(p)}")
        if not changed:
            print(f"ok: code unchanged in {len(state)} file(s)")
            os.remove(_state_path())
        return 1 if changed else 0

    if cmd == "compare" and len(args) == 2:
        reason = unchecked_reason(args[0]) or unchecked_reason(args[1])
        if reason:
            print(f"unchecked ({reason})")
            return 2
        same = fingerprint(args[0]) == fingerprint(args[1])
        print("ok: code unchanged" if same else "CODE CHANGED")
        return 0 if same else 1

    if cmd == "comments" and len(args) == 1:
        _, comments = split(args[0])
        print(json.dumps([{"line": ln, "text": t} for ln, t in comments], indent=1))
        return 0

    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
