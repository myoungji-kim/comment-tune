#!/usr/bin/env python3
"""Prove that an edit changed comments only.

    comment_guard.py snapshot FILE...   record the comment-free code of FILEs
    comment_guard.py verify             report snapshotted files whose code changed
    comment_guard.py compare OLD NEW    compare two files directly
    comment_guard.py comments FILE      print the comments of FILE as JSON

Exit status: 0 when no code changed, 1 when some did, 2 on usage errors.
Whitespace is ignored, so re-indenting or reflowing around a comment is fine.
Standard library only, so the skill runs anywhere python3 does.
"""
import hashlib
import io
import json
import os
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
    ".php": ('"', "'"),
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
SUPPORTED = set(C_LIKE) | set(HASH) | {".py"}


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
        if src.startswith(line_marker, i) and _hash_starts_comment(src, i, line_marker):
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
    if ext in C_LIKE:
        return _lex(src, C_LIKE[ext], "//", ("/*", "*/"))
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
            if os.path.splitext(p)[1].lower() in SUPPORTED:
                state[os.path.abspath(p)] = fingerprint(p)
            else:
                skipped.append(p)
        with open(_state_path(), "w") as f:
            json.dump(state, f)
        print(f"snapshot: {len(state)} file(s)")
        for p in skipped:
            print(f"unchecked (unsupported type): {p}")
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
