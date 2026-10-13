"""Trajectory eval for the HR agent: score the path, not only the answer.

Run:  python -m hr_agent.trajectory_eval --tag baseline            (10 cases x 3 repeats)
      python -m hr_agent.trajectory_eval --compare baseline mitigated

Per run it records outcome pass (value correct) and trajectory pass (tool sequence is one of the
case's accepted paths, every argument is real, and the cited rule was actually retrieved), then
classifies each deviation into the failure-mode taxonomy below. Writes week8_output/trajectory_<tag>.json
and trajectory_<tag>.md; --compare writes week8_output/regression.md.
"""
import argparse
import json
import re
import statistics
from collections import Counter
from pathlib import Path

from hr_agent.agent import run_agent
from hr_agent.tools import DATA_DIR, JURISDICTIONS, TOPICS, _EMPLOYEES, _HANDBOOK
from hr_agent.trajectory_cases import CASES

OUT_DIR = Path(__file__).resolve().parent.parent / "week8_output"

# Every real policy section / rule id: handbook clauses HB-1..HB-6 plus every table rule id.
REAL_SECTIONS = {heading.split(" ")[0] for heading, _ in _HANDBOOK}
REAL_SECTIONS |= {r["rule_id"] for j in json.loads((DATA_DIR / "jurisdiction_rules.json").read_text()).values()
                  for table in j.values() for r in table}
SECTION_REF = re.compile(r"\b(HB-\d+|[A-Z]{2}-[A-Z]{2}-\d+)\b", re.IGNORECASE)

# Failure-mode taxonomy (this agent's slice of the Week 8 zoo).
MODES = {
    "skipped_record": "answered without reading the employee record (tenure/jurisdiction guessed)",
    "skipped_clause": "a required handbook clause (HB-2/3/4/6) was never retrieved; formula assumed",
    "wrong_argument": "real but wrong arguments, e.g. the IN table for a UK transfer, another employee",
    "invented_argument": "an argument that does not exist: unknown employee id, non-enum value, "
                         "fictional section/rule id in a query or in the final citation",
    "unsupported_citation": "final rule_id is real but never appeared in any tool result of the run",
    "redundant_call": "duplicate call, or a call outside every accepted path",
    "order_violation": "right calls, but in an order no accepted path allows",
    "no_answer": "budget fired, error, or output broke the contract",
    "wrong_answer": "final value does not match the expected value (outcome failure)",
}


def _parse_calls(trajectory):
    calls = []
    for c in trajectory:
        try:
            args = json.loads(c["arguments"] or "{}")
            args = args if isinstance(args, dict) else None
        except json.JSONDecodeError:
            args = None
        calls.append({"tool": c["tool"], "args": args, "raw": c["arguments"], "result": c["result"]})
    return calls


def _arg_valid(call) -> bool:
    """Are the arguments real, or fluent fiction?"""
    a = call["args"]
    if a is None:
        return False
    if call["tool"] == "get_employee_record":
        return str(a.get("employee_id", "")).strip().upper() in _EMPLOYEES
    if call["tool"] == "get_jurisdiction_rules":
        return a.get("jurisdiction") in JURISDICTIONS and a.get("topic") in TOPICS
    if call["tool"] == "search_handbook":
        refs = SECTION_REF.findall(str(a.get("query", "")))
        return isinstance(a.get("query"), str) and all(r.upper() in REAL_SECTIONS for r in refs)
    return False  # unknown tool


def score_run(case, run) -> dict:
    calls = _parse_calls(run["trajectory"])
    answer = run["answer"] or {}
    modes = set()

    outcome_pass = run["status"] == "ok" and abs(answer.get("value", float("nan")) - case.expected_value) < 0.01
    if run["status"] != "ok":
        modes.add("no_answer")
    elif not outcome_pass:
        modes.add("wrong_answer")

    # Argument validity: every tool call, plus the policy section cited in the final answer.
    valid_flags = [_arg_valid(c) for c in calls]
    cited = str(answer.get("rule_id", "")).strip().upper()
    if answer:
        valid_flags.append(cited in REAL_SECTIONS)
    if not all(valid_flags):
        modes.add("invented_argument")
    if answer and cited in REAL_SECTIONS and not any(cited in json.dumps(c["result"]).upper() for c in calls):
        modes.add("unsupported_citation")

    # Path checks.
    record_step = next(s for s in case.required if s.tool == "get_employee_record")
    if not any(record_step.matches(c) for c in calls):
        modes.add("skipped_record")
    for step in case.required:
        if step.clause and not any(step.matches(c) for c in calls):
            modes.add("skipped_clause")
    known_steps = case.required + case.optional
    seen = set()
    for c, valid in zip(calls, valid_flags):
        key = (c["tool"], c["raw"])
        if key in seen:
            modes.add("redundant_call")
        seen.add(key)
        if valid and not any(s.matches(c) for s in known_steps):
            modes.add("redundant_call" if c["tool"] == "search_handbook" else "wrong_argument")

    accepted = case.accepted_paths()
    path_ok = any(len(p) == len(calls) and all(s.matches(c) for s, c in zip(p, calls)) for p in accepted)
    if not path_ok:
        max_len = max(len(p) for p in accepted)
        if len(calls) > max_len:
            modes.add("redundant_call")
        elif not modes & {"skipped_record", "skipped_clause", "wrong_argument", "invented_argument", "redundant_call"}:
            modes.add("order_violation")

    trajectory_pass = (run["status"] == "ok" and path_ok
                       and not modes & {"invented_argument", "unsupported_citation"})
    tool_names = {c["tool"] for c in calls}
    tool_choice_ok = any(tool_names == {s.tool for s in p} for p in accepted)

    return {
        "case": case.id, "status": run["status"], "value": answer.get("value"), "expected": case.expected_value,
        "rule_id": answer.get("rule_id"), "outcome_pass": outcome_pass, "trajectory_pass": trajectory_pass,
        "tool_choice_ok": tool_choice_ok, "args_valid": sum(valid_flags), "args_total": len(valid_flags),
        "steps": len(calls), "steps_needed": case.steps_needed,
        "step_efficiency": len(calls) / case.steps_needed,
        "modes": sorted(modes), "cost_usd": run["cost_usd"], "total_tokens": run["total_tokens"],
        "latency_s": run["latency_s"], "laps": run["laps"],
        "path": [f"{c['tool']}({c['raw']})" for c in calls],
    }


def summarise(rows) -> dict:
    n = len(rows)
    costs = [r["cost_usd"] for r in rows]
    tokens = [r["total_tokens"] for r in rows]
    outcome = sum(r["outcome_pass"] for r in rows) / n
    trajectory = sum(r["trajectory_pass"] for r in rows) / n
    return {
        "runs": n,
        "outcome_pass_rate": outcome,
        "trajectory_pass_rate": trajectory,
        "gap": outcome - trajectory,
        "tool_choice_accuracy": sum(r["tool_choice_ok"] for r in rows) / n,
        "argument_validity": sum(r["args_valid"] for r in rows) / max(1, sum(r["args_total"] for r in rows)),
        "step_efficiency_mean": statistics.mean(r["step_efficiency"] for r in rows),
        "step_efficiency_max": max(r["step_efficiency"] for r in rows),
        "cost_p50_usd": statistics.median(costs),
        "cost_max_usd": max(costs),
        "cost_mean_usd": statistics.mean(costs),
        "tokens_p50": statistics.median(tokens),
        "tokens_max": max(tokens),
        "latency_p50_s": statistics.median(r["latency_s"] for r in rows),
        "latency_max_s": max(r["latency_s"] for r in rows),
        "right_answer_wrong_path": sum(r["outcome_pass"] and not r["trajectory_pass"] for r in rows),
        "mode_counts": {m: sum(m in r["modes"] for r in rows) for m in MODES},
    }


def render(tag, summary, rows) -> str:
    s = summary
    lines = [f"# Trajectory eval — {tag}", "",
             f"{s['runs']} runs (10 cases x {s['runs'] // 10} repeats).", "",
             "| metric | value |", "|---|---|",
             f"| outcome pass rate | {s['outcome_pass_rate']:.1%} |",
             f"| trajectory pass rate | {s['trajectory_pass_rate']:.1%} |",
             f"| **gap (outcome - trajectory)** | **{s['gap'] * 100:+.1f} pts** |",
             f"| right answer, wrong path (runs) | {s['right_answer_wrong_path']} |",
             f"| tool-choice accuracy | {s['tool_choice_accuracy']:.1%} |",
             f"| argument validity | {s['argument_validity']:.1%} |",
             f"| step efficiency (taken / needed), mean / max | {s['step_efficiency_mean']:.2f} / {s['step_efficiency_max']:.2f} |",
             f"| cost per question p50 / max | ${s['cost_p50_usd']:.6f} / ${s['cost_max_usd']:.6f} |",
             f"| tokens per question p50 / max | {s['tokens_p50']:.0f} / {s['tokens_max']} |",
             f"| latency p50 / max (s) | {s['latency_p50_s']:.2f} / {s['latency_max_s']:.2f} |",
             "", "## Failure modes (runs showing each mode)", "", "| mode | runs | meaning |", "|---|---|---|"]
    lines += [f"| {m} | {s['mode_counts'][m]} | {MODES[m]} |" for m in MODES]
    lines += ["", "## Runs", "", "| case | outcome | trajectory | value | rule | steps | cost | modes | path |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['case']} | {'PASS' if r['outcome_pass'] else 'FAIL'} | "
                     f"{'PASS' if r['trajectory_pass'] else 'FAIL'} | {r['value']} | {r['rule_id']} | "
                     f"{r['steps']}/{r['steps_needed']} | ${r['cost_usd']:.6f} | {', '.join(r['modes']) or '-'} | "
                     f"{' → '.join(r['path']) or '(no tools)'} |")
    return "\n".join(lines) + "\n"


def run_eval(tag, repeats, only):
    rows = []
    for rep in range(repeats):
        for case in CASES:
            if only and case.id not in only:
                continue
            run = run_agent(case.question)
            row = score_run(case, run)
            row["repeat"] = rep + 1
            rows.append(row)
            print(f"[{tag}] {case.id} r{rep + 1} outcome={'PASS' if row['outcome_pass'] else 'FAIL'} "
                  f"trajectory={'PASS' if row['trajectory_pass'] else 'FAIL'} modes={row['modes']} "
                  f"steps={row['steps']} cost=${row['cost_usd']:.6f}")
    rows.sort(key=lambda r: (r["case"], r["repeat"]))
    summary = summarise(rows)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / f"trajectory_{tag}.json").write_text(json.dumps({"summary": summary, "runs": rows}, indent=1))
    (OUT_DIR / f"trajectory_{tag}.md").write_text(render(tag, summary, rows), encoding="utf-8")
    print(render(tag, summary, rows).split("## Runs")[0])


def compare(before_tag, after_tag):
    before = json.loads((OUT_DIR / f"trajectory_{before_tag}.json").read_text())["summary"]
    after = json.loads((OUT_DIR / f"trajectory_{after_tag}.json").read_text())["summary"]
    lines = [f"# Regression check — {before_tag} -> {after_tag}", "",
             "| failure mode | before | after | change |", "|---|---|---|---|"]
    for m in MODES:
        b, a = before["mode_counts"][m], after["mode_counts"][m]
        flag = "**worse**" if a > b else ("better" if a < b else "same")
        lines.append(f"| {m} | {b} | {a} | {flag} |")
    lines += ["", "| metric | before | after |", "|---|---|---|"]
    for k, fmt in [("outcome_pass_rate", "{:.1%}"), ("trajectory_pass_rate", "{:.1%}"), ("gap", "{:+.3f}"),
                   ("tool_choice_accuracy", "{:.1%}"), ("argument_validity", "{:.1%}"),
                   ("step_efficiency_mean", "{:.2f}"), ("step_efficiency_max", "{:.2f}"),
                   ("cost_p50_usd", "${:.6f}"), ("cost_max_usd", "${:.6f}"), ("cost_mean_usd", "${:.6f}"),
                   ("tokens_p50", "{:.0f}"), ("tokens_max", "{:.0f}"),
                   ("latency_p50_s", "{:.2f}"), ("latency_max_s", "{:.2f}")]:
        lines.append(f"| {k} | {fmt.format(before[k])} | {fmt.format(after[k])} |")
    text = "\n".join(lines) + "\n"
    (OUT_DIR / "regression.md").write_text(text, encoding="utf-8")
    print(text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", default="baseline")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--only", nargs="*")
    p.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    args = p.parse_args()
    if args.compare:
        compare(*args.compare)
    else:
        run_eval(args.tag, args.repeats, args.only)


if __name__ == "__main__":
    main()
