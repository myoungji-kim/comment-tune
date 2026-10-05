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

    python3 evals/run.py --rescore evals/results/RUN.json
        Score the outputs an agent run saved again, after the cases or the
        scorer change. Each agent run saves its outputs next to its JSON.

    python3 evals/run.py --coverage
        Count case items per criteria tag and language, and flag tags with
        too few items to trust a score on.

Metrics per case: noise removed, context kept verbatim and context survived
(not deleted; kept or rewritten in place), the pair that matters most since a
tool that deletes the comments worth keeping is worse than none; stale
comments fixed, expected comments present, forbidden spots left without a
new comment, code changed (must be no), tokens.
"""
import argparse
import datetime
import fnmatch
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
SKILL_PROMPT = "/comment-tune {file} --apply"
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
        "context": found["fill"] + ["untouchable", "todo-with-reason", "clarification"],
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


def code_lines(path, src):
    """Line numbers that hold code, in order."""
    lines = src.splitlines()
    comment_only = set()
    for ln, text in comment_guard.split(str(path), src)[1]:
        trailing = lines[ln - 1].split(text.split("\n", 1)[0], 1)[0].strip() != ""
        comment_only.update(range(ln + trailing, ln + text.count("\n") + 1))
    return [i + 1 for i, l in enumerate(lines) if l.strip() and i + 1 not in comment_only]


def owners(path, src, comments):
    """For each comment, the index of the code line it belongs to: the line it trails, or the next one.

    Code is identical before and after a comment-only edit, so the same index
    names the same spot in both versions of a file.
    """
    code = code_lines(path, src)
    index = {n: k for k, n in enumerate(code)}
    return [index[ln] if ln in index
            else next((index[n] for n in code if n > ln + t.count("\n")), len(code))
            for ln, t in comments]


def score(case, out_path, in_path=None):
    in_path = in_path or CASES / case["name"] / "input" / case["file"]
    src, comments = read_comments(out_path)
    in_src, in_comments = read_comments(in_path)
    before = {norm(t) for _, t in in_comments}

    def matches(item, text):
        if "exact" in item:
            return norm(item["exact"]) == norm(text)
        return norm(item["text"]) in norm(text)

    def present(item):
        return any(matches(item, t) for _, t in comments)

    # Spots where the output has a comment the input didn't: a rewrite lands on one of these.
    rewritten_at = {o for (_, t), o in zip(comments, owners(out_path, src, comments))
                    if norm(t) not in before}
    in_owner = owners(in_path, in_src, in_comments)

    def survived(item):
        """Kept verbatim, or its spot holds a changed comment.

        An upper bound: a rewrite that drops the point, a partial delete of a
        multi-line comment, or a deletion beside another rewrite all pass.
        Whether a rewrite kept the meaning needs a judge, not this scorer.
        """
        if present(item):
            return True
        return any(matches(item, t) and o in rewritten_at
                   for (_, t), o in zip(in_comments, in_owner))

    lines = src.splitlines()
    # A leftover noise or stale comment can't count as the expected one.
    bad = [norm(b.get("exact") or b["text"]) for b in case["noise"] + case["stale"]]
    spans = [(ln, ln + t.count("\n"), norm(t)) for ln, t in comments
             if not any(b in norm(t) for b in bad)]

    added = [(ln, ln + t.count("\n"), norm(t)) for ln, t in comments if norm(t) not in before]

    def lines_ok(item):
        """Lines a comment for this item may end on: above any of its anchors, or inside the statement."""
        anchors = item["anchor"] if isinstance(item["anchor"], list) else [item["anchor"]]
        found = [next((i + 1 for i, l in enumerate(lines) if a in l), None) for a in anchors]
        if None in found:
            return set()
        return {n for a in found for n in range(a - NEAR, a + item.get("lines", 1))}

    def has_comment(exp):
        ok = lines_ok(exp)
        return any(end in ok and any(k.lower() in t for k in exp["any"]) for _, end, t in spans)

    def left_alone(item):
        ok = lines_ok(item)
        return bool(ok) and not any(end in ok for _, end, _ in added)

    checks = {
        "noise_removed": ("noise", lambda n: not present(n)),
        "context_kept": ("context", present),
        "context_survived": ("context", survived),
        "stale_fixed": ("stale", lambda s: not present(s)),
        "expected_comments": ("expect_comment", has_comment),
        "forbid_respected": ("forbid_comment", left_alone),
    }
    result, missed = {}, {}
    for metric, (group, passes) in checks.items():
        failed = [i for i in case[group] if not passes(i)]
        result[metric] = [len(case[group]) - len(failed), len(case[group])]
        if failed:
            missed[metric] = [i.get("exact") or i.get("text") or i["anchor"] for i in failed]
    result["code_changed"] = (comment_guard.fingerprint(str(in_path))
                              != comment_guard.fingerprint(str(out_path), src))
    result["missed"] = missed
    return result


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
    prompt = (SKILL_PROMPT if arm == "skill" else BASELINE_PROMPT).format(file=case["file"])
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


def summarize(rows):
    metrics = [k for k, v in rows[0].items() if isinstance(v, list)] if rows else []
    total = {k: [sum(r[k][0] for r in rows), sum(r[k][1] for r in rows)] for k in metrics}
    summary = {k: f"{v[0]}/{v[1]} ({v[0] / v[1]:.0%})" for k, v in total.items() if v[1]}
    summary["runs_with_code_changes"] = sum(r["code_changed"] for r in rows)
    counted = [r["tokens"] for r in rows if r["tokens"]]
    summary["avg_tokens"] = round(sum(counted) / len(counted)) if counted else None
    return summary


def run_agent(args, names):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS / f"{stamp}-{args.agent}-{args.arm}"
    rows = []
    for name in names:
        case = load_case(name)
        for i in range(args.runs):
            ws = workspace(case)
            tokens, report = run_claude(ws, case, args.arm, args.model)
            # Keep the output so a later scorer can rescore it without another agent run.
            saved = run_dir / f"{name}-{i + 1}" / case["file"]
            saved.parent.mkdir(parents=True)
            shutil.copy(ws / case["file"], saved)
            s = score(case, saved)
            s.update(case=name, run=i + 1, tokens=tokens, report=report,
                     output=saved.relative_to(ROOT).as_posix())
            rows.append(s)
            print(f"{name} #{i + 1}: {fmt(s)}", flush=True)
            if not args.keep:
                shutil.rmtree(ws, ignore_errors=True)
            else:
                print(f"  kept: {ws}")

    summary = summarize(rows)
    print(json.dumps(summary, indent=2))
    out = run_dir.with_suffix(".json")
    out.write_text(json.dumps({"agent": args.agent, "arm": args.arm, "model": args.model,
                               "summary": summary, "runs": rows}, indent=2) + "\n")
    print(f"saved {out.relative_to(ROOT)}")
    return 1 if summary["runs_with_code_changes"] else 0


def rescore(path):
    """Score the saved outputs of an earlier agent run again, with the current cases and scorer."""
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    rows = []
    for old in data["runs"]:
        if "output" not in old:
            sys.exit(f"{path} predates saved outputs; rerun the agent")
        s = score(load_case(old["case"]), ROOT / old["output"])
        s.update(case=old["case"], run=old["run"], tokens=old["tokens"], report=old["report"],
                 output=old["output"])
        rows.append(s)
        print(f"{old['case']} #{old['run']}: {fmt(s)}")
    data.update(summary=summarize(rows), runs=rows)
    print(json.dumps(data["summary"], indent=2))
    pathlib.Path(path).write_text(json.dumps(data, indent=2) + "\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--agent", choices=["claude"])
    ap.add_argument("--arm", choices=["skill", "baseline"], default="skill")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--case", action="append",
                    help="case name or glob such as 'oss-*'; repeatable (default: all)")
    ap.add_argument("--model")
    ap.add_argument("--keep", action="store_true", help="keep temp workspaces")
    ap.add_argument("--score", nargs=2, metavar=("CASE", "FILE"))
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--rescore", metavar="RESULT_JSON")
    args = ap.parse_args()

    names = sorted(p.name for p in CASES.iterdir() if (p / "case.json").exists())
    if args.case:
        names = [n for n in names if any(fnmatch.fnmatch(n, pat) for pat in args.case)]
    if args.selftest:
        return selftest(names)
    if args.coverage:
        return coverage(names)
    if args.rescore:
        return rescore(args.rescore)
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
