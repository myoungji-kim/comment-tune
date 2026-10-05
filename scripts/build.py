#!/usr/bin/env python3
"""Generate the plugin files from the single source in rules/.

    python3 scripts/build.py          write generated files
    python3 scripts/build.py --check  exit 1 if any generated file is stale

rules/core.md               -> AGENTS.md, hooks/session-start.json
rules/skills/*.md           -> skills/<name>/SKILL.md
rules/references/*.md       -> <skill>/references/ (only the ones a skill reads)
tools/comment_guard.py      -> <skill>/scripts/   (comment-tune only)
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "rules"
CORE_MAX_LINES = 50

SKILLS = {
    "comment-tune": {
        "references": ["criteria.md", "examples.md"],
        "scripts": ["tools/comment_guard.py"],
    },
    "comment-tune-audit": {
        "references": ["criteria.md", "patterns.md"],
        "scripts": [],
    },
}


def outputs():
    """Map each generated path (relative to ROOT) to its bytes."""
    core = (RULES / "core.md").read_text(encoding="utf-8")
    lines = core.rstrip("\n").count("\n") + 1
    if lines > CORE_MAX_LINES:
        sys.exit(f"rules/core.md is {lines} lines; the limit is {CORE_MAX_LINES}")

    out = {
        "AGENTS.md": core.encode(),
        "hooks/session-start.json": (json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": core,
            }
        }, indent=2) + "\n").encode(),
    }
    for name, spec in SKILLS.items():
        out[f"skills/{name}/SKILL.md"] = (RULES / "skills" / f"{name}.md").read_bytes()
        for ref in spec["references"]:
            out[f"skills/{name}/references/{ref}"] = (RULES / "references" / ref).read_bytes()
        for script in spec["scripts"]:
            src = ROOT / script
            out[f"skills/{name}/scripts/{src.name}"] = src.read_bytes()
    return out


def generated_dirs():
    return [ROOT / "skills" / name for name in SKILLS]


def main(argv):
    out = outputs()
    stale = [p for p, data in out.items()
             if not (ROOT / p).exists() or (ROOT / p).read_bytes() != data]
    extra = [f.relative_to(ROOT).as_posix() for d in generated_dirs() if d.exists()
             for f in d.rglob("*") if f.is_file() and f.relative_to(ROOT).as_posix() not in out]

    if "--check" in argv:
        for p in stale:
            print(f"stale: {p}")
        for p in extra:
            print(f"not generated: {p}")
        if stale or extra:
            print("run: python3 scripts/build.py")
            return 1
        print(f"ok: {len(out)} generated files up to date")
        return 0

    for p in extra:
        (ROOT / p).unlink()
    for p, data in out.items():
        dest = ROOT / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        if dest.suffix == ".py":
            shutil.copymode(ROOT / "tools" / dest.name, dest)
    print(f"wrote {len(out)} files ({len(stale)} changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
