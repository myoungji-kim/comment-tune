#!/usr/bin/env python3
"""Score comment-tune against seeded source files in several languages.

    python3 evals/run.py --selftest
        Score each case's input (before) and reference (ideal). The reference
        must score perfectly; this proves the scorer and the cases agree.

    python3 evals/run.py --agent claude [--arm skill|baseline] [--runs N]
                         [--case NAME] [--model MODEL]
        Run a real headless agent on each case in a temp git repo and score
        the file it leaves behind. `skill` runs comment-tune --apply;
        `baseline` asks the same agent to clean up comments with no plugin.

    python3 evals/run.py --score CASE FILE
        Score one output file against a case.

    python3 evals/run.py --coverage
        Count case items per criteria tag and language, and flag tags with
        too few items to trust a score on.

Metrics per case: noise removed, context kept (the one that matters most:
a tool that deletes the comments worth keeping is worse than none), stale
comments fixed, expected comments present, forbidden spots left without a
new comment, code changed (must be no), tokens.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases"
RESULTS = ROOT / "evals" / "results"
CRITERIA = ROOT / "rules" / "references" / "criteria.md"
sys.path.insert(0, str(ROOT / "tools"))
import comment_guard  # noqa: E402

NEAR = 3  # a comment counts for an anchor when it ends at most this many lines above it
MIN_PER_TAG = 2  # one item per tag can't tell a skill from luck

BASELINE_PROMPT = (
    "Clean up the code comments in {file}: remove noise, add context that is "
    "missing, and fix comments that no longer match the code. Change comments "
    "only, never code. Apply the changes directly without asking."
)
SKILL_PROMPT = {"claude": "/comment-tune {file} --apply", "codex": "$comment-tune {file} --apply"}
GROUPS = ("noise", "context", "stale", "expect_comment", "forbid_comment")


def norm(text):
    return " ".join(text.split()).lower()


def load_case(name):
    case = json.loads((CASES / name / "case.json").read_text(encoding="utf-8"))
    case["name"] = name
    for group in GROUPS:
        case.setdefault(group, [])
    return case


def criteria_tags():
    """Valid tags for each case group: the criteria tables plus control tags."""
    found, section = {}, None
    for line in CRITERIA.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].split()[0]
        elif m := re.match(r"\| `([\w-]+)` \|", line):
            found.setdefault(section, []).append(m[1])
    return {
        "noise": found["trim"],
        "context": found["fill"] + ["untouchable", "todo-with-reason"],
        "stale": found["fix"],
        "expect_comment": found["fill"],
        "forbid_comment": ["no-evidence", "plain"],
    }


def tag_errors(case, valid):
    return [f"{group}[{i}]: tag {item.get('tag')!r}"
            for group, tags in valid.items()
            for i, item in enumerate(case[group]) if item.get("tag") not in tags]


def read_comments(path):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    comments = []
    for ln, text in comment_guard.split(str(path), src)[1]:
        # Consecutive line comments read as one comment.
        if comments and comments[-1][0] + comments[-1][1].count("\n") + 1 == ln:
            comments[-1] = (comments[-1][0], comments[-1][1] + "\n" + text)
        else:
            comments.append((ln, text))
    return src, comments


def score(case, out_path, in_path=None):
    in_path = in_path or CASES / case["name"] / "input" / case["file"]
    src, comments = read_comments(out_path)
    texts = [norm(t) for _, t in comments]
    before = {norm(t) for _, t in read_comments(in_path)[1]}

    def present(item):
        if "exact" in item:
            return norm(item["exact"]) in texts
        return any(norm(item["text"]) in t for t in texts)

    lines = src.splitlines()
    # A leftover noise or stale comment can't count as the expected one.
    bad = [norm(b.get("exact") or b["text"]) for b in case["noise"] + case["stale"]]
    spans = [(ln, ln + t.count("\n"), norm(t)) for ln, t in comments
             if not any(b in norm(t) for b in bad)]

    added = [(ln, ln + t.count("\n"), norm(t)) for ln, t in comments if norm(t) not in before]

    def anchor_line(item):
        return next((i + 1 for i, l in enumerate(lines) if item["anchor"] in l), None)

    def has_comment(exp):
        anchor = anchor_line(exp)
        if anchor is None:
            return False
        return any(anchor - NEAR <= end <= anchor and any(k.lower() in t for k in exp["any"])
                   for _, end, t in spans)

    def left_alone(item):
        anchor = anchor_line(item)
        return anchor is not None and not any(anchor - NEAR <= end <= anchor for _, end, _ in added)

    return {
        "noise_removed": [sum(not present(n) for n in case["noise"]), len(case["noise"])],
        "context_kept": [sum(present(c) for c in case["context"]), len(case["context"])],
        "stale_fixed": [sum(not present(s) for s in case["stale"]), len(case["stale"])],
        "expected_comments": [sum(has_comment(e) for e in case["expect_comment"]),
                              len(case["expect_comment"])],
        "forbid_respected": [sum(left_alone(f) for f in case["forbid_comment"]),
                             len(case["forbid_comment"])],
        "code_changed": comment_guard.fingerprint(str(in_path))
        != comment_guard.fingerprint(str(out_path), src),
    }


def fmt(s):
    cols = [f"{k} {v[0]}/{v[1]}" for k, v in s.items() if isinstance(v, list) and v[1]]
    cols.append("code CHANGED" if s["code_changed"] else "code unchanged")
    if s.get("tokens") is not None:
        cols.append(f"tokens {s['tokens']:,}")
    return " | ".join(cols)


def perfect(s):
    return all(v[0] == v[1] for v in s.values() if isinstance(v, list)) and not s["code_changed"]


def selftest(names):
    ok = True
    valid = criteria_tags()
    for name in names:
        case = load_case(name)
        for err in tag_errors(case, valid):
            print(f"  FAIL: {name} {err} is not a known tag")
            ok = False
        before = score(case, CASES / name / "input" / case["file"])
        ideal = score(case, CASES / name / "reference" / case["file"])
        print(f"{name}\n  before: {fmt(before)}\n  ideal:  {fmt(ideal)}")
        if not perfect(ideal):
            print("  FAIL: reference must score perfectly")
            ok = False
        if before["noise_removed"][0] or before["stale_fixed"][0] or before["expected_comments"][0]:
            print("  FAIL: input must start with all noise, stale and missing comments")
            ok = False
        if before["context_kept"][0] != before["context_kept"][1]:
            print("  FAIL: every context comment must be in the input")
            ok = False
    print("selftest ok" if ok else "selftest FAILED")
    return 0 if ok else 1


def coverage(names):
    valid = criteria_tags()
    cases = [load_case(n) for n in names]
    langs = sorted({pathlib.Path(c["file"]).suffix for c in cases})
    print(f"coverage: {len(cases)} cases; missing = 0 items, thin = under {MIN_PER_TAG}\n")
    print(" " * 18 + "".join(f"{lang:>7}" for lang in langs) + f"{'total':>7}")
    gaps = []
    for group, tags in valid.items():
        items = [(pathlib.Path(c["file"]).suffix, i["tag"]) for c in cases for i in c[group]]
        print(f"{group} ({len(items)})")
        for tag in tags:
            per = [items.count((lang, tag)) for lang in langs]
            total = sum(per)
            flag = "missing" if total == 0 else "thin" if total < MIN_PER_TAG else ""
            if flag:
                gaps.append(f"{group}/{tag}")
            cells = "".join(f"{n or '-':>7}" for n in per)
            print(f"  {tag:<16}{cells}{total:>7}  {flag}".rstrip())
    print(f"\n{len(gaps)} gaps: {', '.join(gaps)}" if gaps else "\nno gaps")
    return 0


def workspace(case):
    ws = pathlib.Path(tempfile.mkdtemp(prefix=f"ct-{case['name']}-"))
    shutil.copy(CASES / case["name"] / "input" / case["file"], ws / case["file"])
    git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.com"]
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=ws, check=True)
    subprocess.run(git + ["add", "."], cwd=ws, check=True)
    subprocess.run(git + ["commit", "-q", "-m", case["commit_message"]], cwd=ws, check=True)
    return ws


def run_claude(ws, case, arm, model):
    prompt = (SKILL_PROMPT["claude"] if arm == "skill" else BASELINE_PROMPT).format(file=case["file"])
    # User settings would load the user's own plugins and hooks into both arms.
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--setting-sources", "project",
           "--no-session-persistence",
           "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Edit,Write,Glob,Grep"]
    if arm == "skill":
        cmd += ["--plugin-dir", str(ROOT)]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, encoding="utf-8", timeout=900)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(proc.stdout[-2000:], proc.stderr[-2000:], file=sys.stderr)
        return None, None
    usage = result.get("usage", {})
    tokens = sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                           "cache_read_input_tokens", "output_tokens"))
    return tokens, result.get("result")


def run_codex(ws, case, arm, model):
    if arm == "skill":
        shutil.copytree(ROOT / "codex" / "skills", ws / ".agents" / "skills")
        # Keep the copied skill out of the diff the skill would otherwise judge.
        (ws / ".git" / "info" / "exclude").write_text(".agents/\n")
    prompt = (SKILL_PROMPT["codex"] if arm == "skill" else BASELINE_PROMPT).format(file=case["file"])
    cmd = ["codex", "exec", "--json", "--full-auto", prompt]
    if model:
        cmd[2:2] = ["--model", model]
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, encoding="utf-8", timeout=900)
    tokens, report = 0, None
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        usage = event.get("usage")
        if usage:
            tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        item = event.get("item") or {}
        if item.get("type") == "agent_message":
            report = item.get("text")
    return tokens or None, report


def run_agent(args, names):
    runner = {"claude": run_claude, "codex": run_codex}[args.agent]
    rows = []
    for name in names:
        case = load_case(name)
        for i in range(args.runs):
            ws = workspace(case)
            tokens, report = runner(ws, case, args.arm, args.model)
            s = score(case, ws / case["file"])
            s.update(case=name, run=i + 1, tokens=tokens, report=report)
            rows.append(s)
            print(f"{name} #{i + 1}: {fmt(s)}", flush=True)
            if not args.keep:
                shutil.rmtree(ws, ignore_errors=True)
            else:
                print(f"  kept: {ws}")

    total = {k: [sum(r[k][0] for r in rows), sum(r[k][1] for r in rows)]
             for k in ("noise_removed", "context_kept", "stale_fixed", "expected_comments",
                       "forbid_respected")}
    summary = {k: f"{v[0]}/{v[1]} ({v[0] / v[1]:.0%})" for k, v in total.items() if v[1]}
    summary["runs_with_code_changes"] = sum(r["code_changed"] for r in rows)
    counted = [r["tokens"] for r in rows if r["tokens"]]
    summary["avg_tokens"] = round(sum(counted) / len(counted)) if counted else None
    print(json.dumps(summary, indent=2))

    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS / f"{stamp}-{args.agent}-{args.arm}.json"
    out.write_text(json.dumps({"agent": args.agent, "arm": args.arm, "model": args.model,
                               "summary": summary, "runs": rows}, indent=2) + "\n")
    print(f"saved {out.relative_to(ROOT)}")
    return 1 if summary["runs_with_code_changes"] else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--agent", choices=["claude", "codex"])
    ap.add_argument("--arm", choices=["skill", "baseline"], default="skill")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--case", action="append", help="case name; repeatable (default: all)")
    ap.add_argument("--model")
    ap.add_argument("--keep", action="store_true", help="keep temp workspaces")
    ap.add_argument("--score", nargs=2, metavar=("CASE", "FILE"))
    ap.add_argument("--coverage", action="store_true")
    args = ap.parse_args()

    names = args.case or sorted(p.name for p in CASES.iterdir() if (p / "case.json").exists())
    if args.selftest:
        return selftest(names)
    if args.coverage:
        return coverage(names)
    if args.score:
        s = score(load_case(args.score[0]), args.score[1])
        print(fmt(s))
        return 0 if perfect(s) else 1
    if args.agent:
        if not shutil.which(args.agent):
            sys.exit(f"{args.agent} is not on PATH")
        return run_agent(args, names)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
