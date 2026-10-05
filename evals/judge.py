#!/usr/bin/env python3
"""Judge the comments agent runs rewrote or added, blind to which arm wrote them.

    python3 evals/judge.py RESULT.json [RESULT.json ...] [--model MODEL]

From each run's saved output this collects every context comment that was
rewritten in place and every comment added where the input had none. Items
from all given result files are pooled, deduplicated, shuffled and judged
one case at a time by headless Claude against the input file. Arms are
never shown to the judge. Writes evals/results/judge-<stamp>.json and
prints a summary per arm. Verdicts are cached per prompt, so rerunning after
a failure only judges the cases still missing.

The judge is the same model family as the agents it grades; spot-check its
verdicts by hand before trusting them.
"""
import argparse
import collections
import datetime
import hashlib
import json
import random
import subprocess
import sys

import run

CACHE = run.RESULTS / "judge-cache"  # one file per judged prompt, so a failed run resumes
SCHEMA = {
    "type": "object",
    "properties": {"judgments": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "accurate": {"enum": ["yes", "no", "unsure"]},
            "invented": {"enum": ["yes", "no"]},
            "meaning": {"enum": ["kept", "partial", "lost", "n/a"]},
            "value": {"enum": ["better", "same", "worse", "useful", "noise"]},
            "note": {"type": "string"},
        },
        "required": ["id", "accurate", "invented", "meaning", "value", "note"],
    }}},
    "required": ["judgments"],
}

PROMPT = """You are reviewing code comments that a tool wrote into the file below.
The code itself is unchanged. Judge each item on its own.

Item kinds:
- rewrite: an existing comment was replaced. "original" is the old text, "new" the replacement.
- added: a comment was added where the file had none. "new" is the text.
"line" is where the item sits in the file below: the original comment's first
line for a rewrite, the code line the added comment sits on or above for added.

For every item give:
- accurate: does "new" agree with the code? yes / no / unsure.
- invented: yes if "new" states a reason, history, issue number, or outside fact
  that is neither in the file nor in "original" nor common knowledge about the
  language or platform, so it could be made up. Otherwise no.
- meaning: rewrite only. Does "new" keep every point of "original" that a reader
  needs? kept / partial / lost. Use n/a for added.
- value: rewrite: better / same / worse than "original" for the next reader.
  added: useful (says something the code can't) or noise (restates the code,
  or adds nothing a reader needs).
- note: a few words on why, especially for anything other than accurate=yes,
  invented=no, meaning=kept.

File `{file}` (line numbers added):
{numbered}

Items:
{items}
"""


def collect(result_paths):
    """Unique items per case: {case: {key: item}}, each item remembering which arms produced it."""
    cases = collections.defaultdict(dict)
    for path in result_paths:
        data = json.loads(open(path, encoding="utf-8").read())
        for r in data["runs"]:
            case = run.load_case(r["case"])
            inp = run.CASES / r["case"] / "input" / case["file"]
            out = run.ROOT / r["output"]
            in_src, in_com = run.read_comments(inp)
            out_src, out_com = run.read_comments(out)
            in_owner = run.owners(inp, in_src, in_com)
            out_owner = run.owners(out, out_src, out_com)
            before = {run.norm(t) for _, t in in_com}
            in_code = run.code_lines(inp, in_src)
            new_at = collections.defaultdict(list)
            for (_, t), o in zip(out_com, out_owner):
                if run.norm(t) not in before:
                    new_at[o].append(t)
            spot_line = {o: ln for (ln, _), o in zip(in_com, in_owner)}

            def add(kind, line, original, new):
                key = (kind, line, run.norm(original or ""), run.norm(new))
                item = cases[r["case"]].setdefault(key, {
                    "kind": kind, "line": line, "original": original, "new": new,
                    "arms": collections.Counter()})
                item["arms"][data["arm"]] += 1

            for (ln, t), o in zip(in_com, in_owner):
                is_context = any(run.norm(c.get("exact") or c["text"]) in run.norm(t)
                                 for c in case["context"])
                if is_context and run.norm(t) not in {run.norm(x) for _, x in out_com} and new_at.get(o):
                    add("rewrite", ln, t, "\n".join(new_at[o]))
            for o, texts in new_at.items():
                if o not in spot_line:
                    line = in_code[o] if o < len(in_code) else len(in_src.splitlines())
                    add("added", line, None, "\n".join(texts))
    return cases


def judge_case(name, items, model):
    case = run.load_case(name)
    src = (run.CASES / name / "input" / case["file"]).read_text(encoding="utf-8")
    numbered = "\n".join(f"{i + 1:4} {l}" for i, l in enumerate(src.splitlines()))
    listing = []
    for i, item in enumerate(items):
        entry = {"id": str(i), "kind": item["kind"], "line": item["line"], "new": item["new"]}
        if item["original"]:
            entry["original"] = item["original"]
        listing.append(entry)
    prompt = PROMPT.format(file=case["file"], numbered=numbered, items=json.dumps(listing, indent=1))
    cache = CACHE / f"{hashlib.sha256((prompt + str(model)).encode()).hexdigest()[:16]}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    # The prompt goes on stdin: a large file overflows the Windows command-line limit.
    cmd = ["claude", "-p", "--output-format", "json", "--setting-sources", "project",
           "--no-session-persistence", "--json-schema", json.dumps(SCHEMA)]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                          timeout=900)
    verdicts = {j["id"]: j for j in json.loads(proc.stdout)["structured_output"]["judgments"]}
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(verdicts, ensure_ascii=False), encoding="utf-8")
    return verdicts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="+")
    ap.add_argument("--model")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    judged = []
    for name, by_key in sorted(collect(args.results).items()):
        items = list(by_key.values())
        rng.shuffle(items)
        verdicts = judge_case(name, items, args.model)
        for i, item in enumerate(items):
            v = verdicts.get(str(i), {})
            judged.append({**item, "case": name, "arms": dict(item["arms"]), "verdict": v})
        print(f"{name}: {len(items)} items judged", flush=True)

    summary = {}
    for arm in sorted({a for j in judged for a in j["arms"]}):
        mine = [j for j in judged if arm in j["arms"]]
        s = {}
        for kind in ("rewrite", "added"):
            group = [j for j in mine if j["kind"] == kind]
            counts = collections.Counter()
            for j in group:
                v = j["verdict"]
                counts[f"accurate={v.get('accurate')}"] += 1
                counts[f"invented={v.get('invented')}"] += 1
                counts[f"value={v.get('value')}"] += 1
                if kind == "rewrite":
                    counts[f"meaning={v.get('meaning')}"] += 1
            s[kind] = {"unique": len(group), **dict(sorted(counts.items()))}
        summary[arm] = s
    print(json.dumps(summary, indent=2))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = run.RESULTS / f"judge-{stamp}.json"
    out.write_text(json.dumps({"results": args.results, "model": args.model, "summary": summary,
                               "items": judged}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"saved {out.relative_to(run.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
