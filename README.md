# AI-Week_8 — trajectory evals for the HR agent

Week 8 · Agent Failure Modes & Trajectory Evals · Task Set C (HR policy). Extends the Week 7 HR
agent below: score the *path*, not just the answer, expose the outcome-vs-trajectory gap as a
number, and kill the worst failure mode with its price measured.

Full write-up — expected sequences, numbers, gap trace, mitigation, regression table: **[WEEK8.md](WEEK8.md)**.

## Week 8 results

| metric | baseline (30 runs) |
|---|---|
| tool-choice accuracy | 90.0% |
| argument validity | 100.0% |
| step efficiency, mean / max | 1.07 / 1.50 |
| cost per question, p50 / max | $0.000196 / $0.000327 |
| outcome pass / trajectory pass | 100.0% / 90.0% |
| **gap** | **+10.0 pts** |

**Right answer, wrong path:** C04 *"How many annual leave days does E102 have left?"* answered 17
correctly in every run without ever retrieving HB-4, the only clause that defines the carry-over
balance formula. Path: `get_employee_record -> get_jurisdiction_rules -> answer`.

**One mitigation, re-planning:** before accepting an answer, a check refuses it once if the record
shows a fact (carry-over, part-time, transfer, contractor) whose handbook clause was never read.
Top mode `skipped_clause` 1 -> 0, gap +10 -> 0 pts (repeat 1, 10 vs 10 runs). Price on C04:
+2,078 tokens (+97%), +$0.000184 (+93%), +3.1 s; other 9 cases unchanged. No mode regressed.
A first attempt (tighter tool description) made 3 modes worse and was reverted; see WEEK8.md.

```bash
python -m hr_agent.trajectory_eval --tag baseline --repeats 3
python -m hr_agent.trajectory_eval --compare baseline mitigated --repeat 1
```

---

# Week 7 — HR agent vs fixed workflow

Week 7 · Agent Loops — and When Not to Use Them · Task Set C (HR policy).

A hand-built HR entitlement agent (tool-calling loop) answers questions such as *"What notice period
applies if E104 resigns?"* by finding the employee record, reading tenure and jurisdiction, pulling
the matching handbook rule and computing the answer. The same task is re-implemented as a fixed
workflow (hard-coded steps, no loop), and the two are raced over the same 10 questions to decide,
with numbers, whether the task needs an agent at all.

Full write-up — race table, budget log, tool diff and verdict: **[WEEK7.md](WEEK7.md)**.

## Week 7 results

| system | pass rate | p50 latency (s) | total tokens (10 questions) | cost / question (USD) |
|---|---|---|---|---|
| agent | **100%** | 2.16 | 24,870 | $0.000226 |
| workflow | 90% | **1.13** | **10,373** | **$0.000107** |

Model for both: `openai/gpt-oss-20b` on Groq. Tokens are summed over every LLM call.

**Verdict:** the path does not vary by input for 9 of 10 questions (tenure bands, part-time,
contractor), so the workflow wins there at about half the latency, tokens and cost. The one class
that forces an agent is the **cross-jurisdiction transfer**: the jurisdiction whose rules apply is
only known after reading the record and the transfer clause, and the fixed workflow fetched the
wrong one. Ship the workflow; route transfer questions to the agent (or add one transfer branch).

## Run it (Week 7)

```bash
pip install -r requirements.txt
cp .env.example .env        # then set GROQ_API_KEY

python -m hr_agent.agent "How many paid sick days does E106 get?"      # agent
python -m hr_agent.workflow "How many paid sick days does E106 get?"   # fixed workflow
python -m hr_agent.race          # race over 10 questions -> week7_output/race.csv, race_runs.csv
python -m hr_agent.budget_demo   # tight budgets -> week7_output/budget_termination.log
```

Agent budgets can be set per run:
`python -m hr_agent.agent --max-iters 6 --max-tokens 20000 --max-cost 0.003 --max-wall-s 90 --log run.log "..."`

## Layout

```
hr_agent/
  agent.py            tool-calling loop; max iterations, tokens, cost and wall-clock enforced every lap
  workflow.py         same tools, model and output contract; 2 LLM calls + 3 tool calls, no loop
  tools.py            get_employee_record, search_handbook, get_jurisdiction_rules (enum params)
  contract.py         shared system prompt and output contract (JSON with rule_id + value)
  llm.py              Groq wrapper: per-call tokens, cost, latency, rate-limit backoff, deadline
  race.py             agent vs workflow over questions.json (Week 7)
  trajectory_cases.py the 10 Week 8 cases with accepted tool sequences
  trajectory_eval.py  Week 8 trajectory scorer, failure modes, regression compare
  budget_demo.py      makes each budget fire once and logs the clean termination
  questions.json      10 questions: single lookup, tenure branches, part-time, transfer, contractor
  data/               employees.json, jurisdiction_rules.json, handbook.md (fictional Northwind)
week7_output/
  race.csv            the 8 numbers (4 per system)
  race_runs.csv       per-question value, rule, laps, tokens, latency and tool trace
  budget_termination.log
  tool_description.diff
week8_output/          trajectory_*.md/.json, regression*.md, mitigation.diff, attempt1_description.diff
```

## Week 7 deliverables checklist

- [x] Agent and workflow each runnable by one command
- [x] [race.csv](week7_output/race.csv) with all 8 numbers over the same 10 employee questions
- [x] [Budget termination log](week7_output/budget_termination.log) showing which budget fired (all four)
- [x] [Diff](week7_output/tool_description.diff) of the third tool's description and parameter enums
- [x] Verdict naming the question class that needs an agent ([WEEK7.md](WEEK7.md#5-verdict))

## Earlier weeks in this repo

The FastAPI RAG service and the Week 4 retrieval evaluation (dense vs hybrid) are still here:

```bash
python -m scripts.ingest_corpus   # chunks data/corpus -> data/chunks.json (+ Pinecone if PINECONE_API_KEY set)
python -m scripts.run_eval        # dense vs hybrid, writes eval_output/
uvicorn app.main:app --reload     # run the API
```

Results: [results.md](results.md). Config (see `.env.example`): `RETRIEVAL_MODE` = `dense` | `hybrid`,
`DENSE_BACKEND` = `pinecone` | `local`, `PINECONE_NAMESPACE`.
