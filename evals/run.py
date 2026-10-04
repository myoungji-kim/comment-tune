#!/usr/bin/env python3
"""Score comment-tune against seeded Java, Dart and TypeScript files.

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

Metrics per case: noise removed, context kept (the one that matters most:
a tool that deletes the comments worth keeping is worse than none), stale
comments fixed, expected comments present, code changed (must be no), tokens.
"""
import argparse
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases"
RESULTS = ROOT / "evals" / "results"
sys.path.insert(0, str(ROOT / "tools"))
import comment_guard  # noqa: E402

NEAR = 3  # an expected comment must end at most this many lines above its anchor

BASELINE_PROMPT = (
    "Clean up the code comments in {file}: remove noise, add context that is "
    "missing, and fix comments that no longer match the code. Change comments "
    "only, never code. Apply the changes directly without asking."
)
SKILL_PROMPT = {"claude": "/comment-tune {file} --apply", "codex": "$comment-tune {file} --apply"}


def norm(text):
    return " ".join(text.split()).lower()


def load_case(name):
    case = json.loads((CASES / name / "case.json").read_text())
    case["name"] = name
    return case


def score(case, out_path, in_path=None):
    in_path = in_path or CASES / case["name"] / "input" / case["file"]
    src = pathlib.Path(out_path).read_text()
    comments = []
    for ln, text in comment_guard.split(str(out_path), src)[1]:
        # Consecutive line comments read as one comment.
        if comments and comments[-1][0] + comments[-1][1].count("\n") + 1 == ln:
            comments[-1] = (comments[-1][0], comments[-1][1] + "\n" + text)
        else:
            comments.append((ln, text))
    texts = [norm(t) for _, t in comments]

    def present(item):
        if isinstance(item, dict):
            return norm(item["exact"]) in texts
        return any(norm(item) in t for t in texts)

    lines = src.splitlines()
    # A leftover noise or stale comment can't count as the expected one.
    bad = [norm(b["exact"] if isinstance(b, dict) else b) for b in case["noise"] + case["stale"]]
    spans = [(ln, ln + t.count("\n"), norm(t)) for ln, t in comments
             if not any(b in norm(t) for b in bad)]

    def has_comment(exp):
        anchor = next((i + 1 for i, l in enumerate(lines) if exp["anchor"] in l), None)
        if anchor is None:
            return False
        return any(anchor - NEAR <= end <= anchor and any(k.lower() in t for k in exp["any"])
                   for _, end, t in spans)

    return {
        "noise_removed": [sum(not present(n) for n in case["noise"]), len(case["noise"])],
        "context_kept": [sum(present(c) for c in case["context"]), len(case["context"])],
        "stale_fixed": [sum(not present(s) for s in case["stale"]), len(case["stale"])],
        "expected_comments": [sum(has_comment(e) for e in case["expect_comment"]),
                              len(case["expect_comment"])],
        "code_changed": comment_guard.fingerprint(str(in_path))
        != comment_guard.fingerprint(str(out_path), src),
    }


def fmt(s):
    cols = [f"{k} {v[0]}/{v[1]}" for k, v in s.items() if isinstance(v, list)]
    cols.append("code CHANGED" if s["code_changed"] else "code unchanged")
    if s.get("tokens") is not None:
        cols.append(f"tokens {s['tokens']:,}")
    return " | ".join(cols)


def perfect(s):
    return all(v[0] == v[1] for v in s.values() if isinstance(v, list)) and not s["code_changed"]


def selftest(names):
    ok = True
    for name in names:
        case = load_case(name)
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


def workspace(case):
    ws = pathlib.Path(tempfile.mkdtemp(prefix=f"ct-{case['name']}-"))
    shutil.copy(CASES / case["name"] / "input" / case["file"], ws / case["file"])
    git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.com"]
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(git + ["add", "."], cwd=ws, check=True)
    subprocess.run(git + ["commit", "-q", "-m", case["commit_message"]], cwd=ws, check=True)
    return ws


def run_claude(ws, case, arm, model):
    prompt = (SKILL_PROMPT["claude"] if arm == "skill" else BASELINE_PROMPT).format(file=case["file"])
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Edit,Write,Glob,Grep"]
    if arm == "skill":
        cmd += ["--plugin-dir", str(ROOT)]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=900)
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
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=900)
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
             for k in ("noise_removed", "context_kept", "stale_fixed", "expected_comments")}
    summary = {k: f"{v[0]}/{v[1]} ({v[0] / v[1]:.0%})" for k, v in total.items()}
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
    args = ap.parse_args()

    names = args.case or sorted(p.name for p in CASES.iterdir() if (p / "case.json").exists())
    if args.selftest:
        return selftest(names)
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
