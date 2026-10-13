"""Hand-built HR entitlement agent: a tool-calling loop over the HR tools, under four budgets.

Run:  python -m hr_agent.agent "How many sick days does E106 get?"
      python -m hr_agent.agent --max-tokens 3000 --log run.log "..."

Budgets are checked before every lap. The token and cost checks are projected: each lap
re-sends the whole message list, so the next lap costs at least as much as the last one, and
the loop stops *before* a lap that would cross the cap instead of after it. Wall-clock is
enforced inside the call too (request timeout = time left; see llm.chat).
"""
import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass

from groq import APIError

from hr_agent import llm
from hr_agent.contract import SYSTEM_PROMPT, parse_answer
from hr_agent.tools import TOOL_SCHEMAS, call_tool

log = logging.getLogger("hr_agent.agent")


@dataclass
class Budget:
    max_iters: int = 6
    max_tokens: int = 20_000
    max_cost_usd: float = 0.003
    max_wall_s: float = 90.0


def _assistant_message(msg) -> dict:
    out = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        out["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]
    return out


def _budget_fired(budget: Budget, laps: int, used: dict, last: dict, elapsed: float):
    """Return (budget_name, detail) for the first budget the next lap would break, else None."""
    if laps >= budget.max_iters:
        return "max_iters", f"{laps} laps done, limit {budget.max_iters}"
    if used["total_tokens"] + last["total_tokens"] > budget.max_tokens:
        return "max_tokens", (f"used {used['total_tokens']} + next lap >= {last['total_tokens']} "
                              f"> limit {budget.max_tokens}")
    if used["cost_usd"] + last["cost_usd"] > budget.max_cost_usd:
        return "max_cost", (f"spent ${used['cost_usd']:.6f} + next lap >= ${last['cost_usd']:.6f} "
                            f"> limit ${budget.max_cost_usd:.6f}")
    if elapsed >= budget.max_wall_s:
        return "wall_clock", f"{elapsed:.1f}s elapsed, limit {budget.max_wall_s:.1f}s"
    return None


def run_agent(question: str, budget: Budget = None) -> dict:
    budget = budget or Budget()
    start = time.perf_counter()
    deadline = start + budget.max_wall_s
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    zero = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
    used = {**zero, "backoff_s": 0.0}
    last = dict(zero)
    tool_trace = []
    trajectory = []  # every tool call with its raw arguments and result, for the trajectory eval
    laps = 0
    log.info("START question=%r budget=%s", question, asdict(budget))

    def finish(status, answer=None, error=None):
        wall = time.perf_counter() - start
        result = {"status": status, "answer": answer, "laps": laps, "tool_calls": tool_trace,
                  "trajectory": trajectory, "error": error,
                  **{k: used[k] for k in zero}, "backoff_s": used["backoff_s"],
                  "latency_s": wall - used["backoff_s"]}
        log.info("END status=%s laps=%d tokens=%d cost=$%.6f latency=%.2fs",
                 status, laps, used["total_tokens"], used["cost_usd"], result["latency_s"])
        return result

    while True:
        fired = _budget_fired(budget, laps, used, last, time.perf_counter() - start)
        if fired:
            name, detail = fired
            log.warning("BUDGET FIRED: %s (%s) -> terminating cleanly before lap %d", name, detail, laps + 1)
            return finish(f"budget:{name}")

        try:
            msg, usage = llm.chat(messages, tools=TOOL_SCHEMAS, deadline=deadline)
        except llm.DeadlineExceeded as e:
            log.warning("BUDGET FIRED: wall_clock (%s) -> terminating cleanly during lap %d", e, laps + 1)
            return finish("budget:wall_clock")
        except APIError as e:
            log.error("LLM error on lap %d: %s", laps + 1, e)
            return finish("error", error=str(e)[:500])

        laps += 1
        for k in zero:
            used[k] += usage[k]
            last[k] = usage[k]
        used["backoff_s"] += usage["backoff_s"]
        messages.append(_assistant_message(msg))
        log.info("lap %d: +%d tokens (prompt %d) -> total %d tokens, $%.6f, %.1fs elapsed",
                 laps, usage["total_tokens"], usage["prompt_tokens"], used["total_tokens"],
                 used["cost_usd"], time.perf_counter() - start)

        if not msg.tool_calls:
            answer = parse_answer(msg.content)
            return finish("ok" if answer else "bad_output", answer)

        for tc in msg.tool_calls:
            result = call_tool(tc.function.name, tc.function.arguments)
            tool_trace.append(f"{tc.function.name}({tc.function.arguments})")
            trajectory.append({"tool": tc.function.name, "arguments": tc.function.arguments, "result": result})
            log.info("lap %d: tool %s(%s)", laps, tc.function.name, tc.function.arguments)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})


def main():
    p = argparse.ArgumentParser(description="HR entitlement agent (tool-calling loop)")
    p.add_argument("question", nargs="+")
    d = Budget()
    p.add_argument("--max-iters", type=int, default=d.max_iters)
    p.add_argument("--max-tokens", type=int, default=d.max_tokens)
    p.add_argument("--max-cost", type=float, default=d.max_cost_usd)
    p.add_argument("--max-wall-s", type=float, default=d.max_wall_s)
    p.add_argument("--log", help="also write the run log to this file")
    args = p.parse_args()

    handlers = [logging.StreamHandler()]
    if args.log:
        handlers.append(logging.FileHandler(args.log, mode="w", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    budget = Budget(args.max_iters, args.max_tokens, args.max_cost, args.max_wall_s)
    print(json.dumps(run_agent(" ".join(args.question), budget), indent=2))


if __name__ == "__main__":
    main()
