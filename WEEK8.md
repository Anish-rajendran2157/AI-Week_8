# Week 8 — Task Set C: the outcome-vs-trajectory gap in the HR agent

Week 8 · Agent Failure Modes & Trajectory Evals. Extends the Week 7 HR agent (same tools, model
`openai/gpt-oss-20b` on Groq, `temperature=0`, same output contract).

```bash
python -m hr_agent.trajectory_eval --tag baseline --repeats 3          # score 10 cases x N repeats
python -m hr_agent.trajectory_eval --compare baseline mitigated --repeat 1   # per-mode regression table
```

| File | What it is |
|---|---|
| [hr_agent/trajectory_cases.py](hr_agent/trajectory_cases.py) | The 10 cases and their expected tool sequences, alternates accepted as a set |
| [hr_agent/trajectory_eval.py](hr_agent/trajectory_eval.py) | Scorer: 4 trajectory numbers, gap, failure-mode classifier, regression compare |
| [week8_output/trajectory_baseline.md](week8_output/trajectory_baseline.md) | Baseline: 30 runs with every path |
| [week8_output/trajectory_mitigated.md](week8_output/trajectory_mitigated.md) | After the mitigation (13 valid runs, see §6) |
| [week8_output/mitigation.diff](week8_output/mitigation.diff) | The single shipped mitigation |
| [week8_output/regression.md](week8_output/regression.md) | Per-mode regression table, baseline -> mitigated |
| [week8_output/trajectory_attempt1_description.md](week8_output/trajectory_attempt1_description.md), [regression_attempt1.md](week8_output/regression_attempt1.md), [attempt1_description.diff](week8_output/attempt1_description.diff) | A first mitigation that was measured, made things worse, and was reverted |

## 1. Ten expected tool sequences (alternates marked)

`R` = `get_employee_record`, `T` = `get_jurisdiction_rules(jurisdiction, topic)`,
`S→HB-n` = a `search_handbook` call whose result contains clause HB-n (any wording of the query),
`S?` = one optional exception-check search. Accepted paths are generated in code from required +
optional steps (`Case.accepted_paths`), and a run passes if it equals any one of them.

| case | question (short) | required | alternates accepted (marked ★) | # accepted paths |
|---|---|---|---|---|
| C01 | E106 "in our California office", sick days | R, T(US-CA, sick) | ★ T before R (jurisdiction is in the question); ★ + S? | 8 |
| C02 | E101 notice period | R → T(IN, notice) | ★ + S? anywhere after R | 3 |
| C03 | E103 "over two years in London", notice | R, T(UK, notice) | ★ T before R; ★ + S? | 8 |
| C04 | E102 annual leave **left** | R → T(IN, annual), S→HB-4 | ★ T and S in either order | 2 |
| C05 | E103 sick days | R → T(UK, sick) | ★ + S? | 3 |
| C06 | E107 sick days (probation) | R → T(SG, sick) | ★ + S? | 3 |
| C07 | E105 annual entitlement | R → T(US-CA, annual) | ★ + S? | 3 |
| C08 | E109 annual entitlement (part-time) | R → T(UK, annual), S→HB-6 | ★ T and S in either order | 2 |
| C09 | E108 notice after IN→UK transfer | R → T(**UK**, notice), S→HB-2 | ★ T and S in either order | 2 |
| C10 | E110 annual leave (contractor) | R → S→HB-3 | ★ + T(SG, annual): valid but unneeded | 3 |

Why the alternates: reading the handbook before or after the rule table is equally correct, an
exception-check search on a plain full-time question is prudent, not wrong, and when the question
names the jurisdiction the table can be fetched before the record. The record itself is never
optional, because it is the only authoritative source of tenure, FTE, employment type and transfers. Without
the alternates, the Week 7 traces of C05, C08, C09 and C10 would score as failures and inflate the gap.

C01 and C03 are lures. The question hands over the jurisdiction, and in C03 a tenure ("over two
years") that is false: the record says 20 months. Trusting the question gives UK-NP-2 =
max(28, 7×2) = 28, the same as the true UK-NP-1 = 28, so only the trajectory can show whether
tenure was read.

## 2. Trajectory numbers (baseline, 30 runs = 10 cases × 3 repeats)

| metric | baseline |
|---|---|
| tool-choice accuracy (tools used = an accepted path's tools) | 90.0% |
| argument validity (employee ids, enums, section ids in queries and the final citation are real) | 100.0% (102/102) |
| step efficiency (steps taken / steps needed), mean / max | 1.07 / 1.50 |
| cost per question, p50 / max | $0.000196 / $0.000327 |
| tokens per question, p50 / max | 2,152 / 3,458 |
| outcome pass rate | 100.0% |
| trajectory pass rate | 90.0% |

Cost is every LLM call summed (each lap re-sends the full history). Max is 1.67× p50: the
spread comes from the 4-lap questions (C03, C05, C08, C09), not from a runaway loop. The worst
question cost $0.000327 against a mean of $0.000234.

## 3. The gap: **+10.0 points** (outcome 100.0% − trajectory 90.0%)

**Right answer, wrong path, C04:** *"How many annual leave days does E102 have left this year?"*
Expected 17. All 3 baseline runs answered 17, cited IN-AL-3, and passed the outcome eval:

```
get_employee_record({"employee_id":"E102"})
-> get_jurisdiction_rules({"jurisdiction":"IN","topic":"annual_leave"})
-> answer 17 (IN-AL-3)
```

The balance formula, entitlement + carry_over_days − taken, exists only in handbook clause HB-4,
and the agent never retrieved it. It saw a `carry_over_days` field in the record and *guessed the
common formula*. Here the guess matches the policy. If HB-4 capped carry-over below the record
value or excluded it, the same path would still answer 17 with a confident rule citation, and the
outcome eval would still pass. Failure mode: **skipped_clause** (3/30 runs, all on C04).

The lures did not catch this agent: it read the record first in every run (skipped_record = 0).

## 4. Failure-mode taxonomy and the one mitigation

| mode | meaning |
|---|---|
| skipped_record | answered without reading the employee record (tenure/jurisdiction guessed) |
| skipped_clause | a required handbook clause (HB-2/3/4/6) was never retrieved; formula assumed |
| wrong_argument | real but wrong arguments, e.g. the IN table for a UK transfer |
| invented_argument | unknown employee id, non-enum value, fictional section id in a query or citation |
| unsupported_citation | cited rule is real but never appeared in any tool result of the run |
| redundant_call | duplicate call, or a call outside every accepted path |
| order_violation | right calls in an order no accepted path allows |
| malformed_tool_call | provider rejected the model's tool call (HTTP 400 `tool_use_failed`) |
| no_answer | budget fired, other error, or broken output contract |
| wrong_answer | outcome failure |

**Top mode: skipped_clause.** **Mitigation shipped: re-planning** ([mitigation.diff](week8_output/mitigation.diff)).
When the model returns a final answer, a deterministic check compares facts in the record it read
against the clauses it retrieved: carry-over on an annual-leave answer needs HB-4, part-time needs
HB-6, a transfer needs HB-2, a contractor needs HB-3. If a clause is missing, the answer is refused
once (`MAX_REPLANS = 1`) and the model is told which fact needs which clause. Tools, descriptions,
prompt and model are unchanged.

C04 after the mitigation:

```
get_employee_record(E102) -> get_jurisdiction_rules(IN, annual_leave) -> [answer refused:
"carry_over_days=3 ... clause HB-4 never retrieved"] -> search_handbook("HB-4 carry-over") -> answer 17
```

### Before -> after (repeat 1: same 10 cases, 10 runs each)

| | before | after |
|---|---|---|
| **skipped_clause (top mode)** | **1** | **0** |
| trajectory pass rate | 90.0% | 100.0% |
| outcome pass rate | 100.0% | 100.0% |
| gap | +10.0 pts | 0.0 pts |

### Price paid (measured)

| | before | after | price |
|---|---|---|---|
| C04 laps / tool calls | 3 / 2 | 5 / 3 | +2 LLM laps, +1 tool call |
| C04 tokens | 2,153 | 4,231 | **+2,078 (+97%)** |
| C04 cost | $0.000197 | $0.000381 | **+$0.000184 (+93%)** |
| C04 latency | 2.11 s | 5.22 s | **+3.11 s** |
| all 10: mean cost / question | $0.000234 | $0.000252 | +$0.000018 (+7.9%) |
| all 10: cost p50 / max | $0.000196 / $0.000320 | $0.000238 / $0.000381 | max +19% |
| all 10: tokens p50 / max | 2,152 / 3,436 | 2,678 / 4,231 | |
| step efficiency, mean | 1.07 | 1.10 | |

The re-plan fired on C04 only; the other 9 cases used identical laps and tokens. The p50 jump is
a median artefact: C04 moved from the cheap half of the 10 runs to the expensive half. The price is
paid only by questions whose record carries an adjusting fact. It is not free, though: every such
question that skips its clause now pays roughly double. A further cost is flexibility: an
annual-leave *entitlement* question for someone with carry-over will also be forced to read HB-4,
even though it does not need it.

## 5. Regression check (per mode, baseline -> mitigated, repeat 1)

| failure mode | before | after | change |
|---|---|---|---|
| skipped_record | 0 | 0 | same |
| skipped_clause | 1 | 0 | better |
| wrong_argument | 0 | 0 | same |
| invented_argument | 0 | 0 | same |
| unsupported_citation | 0 | 0 | same |
| redundant_call | 0 | 0 | same |
| order_violation | 0 | 0 | same |
| malformed_tool_call | 0 | 0 | same |
| no_answer | 0 | 0 | same |
| wrong_answer | 0 | 0 | same |

No mode got worse and no new mode appeared; all 10 modes above were checked.

### The mitigation that was not shipped (attempt 1, measured and reverted)

The first thing tried was the "obvious" fix: a tighter `search_handbook` description saying the
clauses are the only source for carry-over, part-time, transfer and contractor adjustments
([diff](week8_output/attempt1_description.diff)). Over 30 runs it made things worse
([regression_attempt1.md](week8_output/regression_attempt1.md)):

| mode | baseline | attempt 1 |
|---|---|---|
| skipped_clause | 3 | **6** (C04 still 3/3; C09 newly skipped HB-2 in 3/3, still answering 28) |
| no_answer | 0 | **2**: C04 now *tried* to read HB-4, but gpt-oss emitted the tool name `search_handbook<|channel|>commentary` and Groq rejected it (`400 tool_use_failed`); reproduced 2/2 |
| wrong_answer | 0 | **2**: C08 picked the < 24-month band (15 instead of 16.5) |
| outcome / trajectory pass | 100% / 90% | 86.7% / 80% |

It was reverted before the re-planning change, so the shipped code has exactly one mitigation.
Lesson: a description edit perturbs every question's path, not only the one it targets. The
re-planning check acts only when its condition holds.

## 6. Caveats

- **The after-numbers use 10 runs, not 30.** The re-planning re-run hit Groq's free-tier daily
  token cap (200k tokens/day for gpt-oss-20b) after 13 of 30 runs. The 17 throttled runs never got
  a model answer (HTTP 429, retry-after past the 90 s wall-clock budget). They are listed in
  `trajectory_mitigated.json` → `excluded_runs` and not scored, because quota is not agent behaviour.
  The eval now aborts on provider throttling instead of scoring it. Before -> after compares
  repeat 1, which is complete for both. The 3 valid repeat-2 runs (C01–C03) also passed both evals.
- At `temperature=0` the baseline repeats were identical (same 3 C04 failures, same paths), which is
  why repeat 1 is representative of the baseline. Attempt 1 showed that a changed prompt *can*
  vary across repeats (C08 2/3 wrong). Re-run the full 30 when quota allows:
  `python -m hr_agent.trajectory_eval --tag mitigated --repeats 3`.
- Prices: $0.075 / 1M input, $0.30 / 1M output (third-party trackers for Groq gpt-oss-20b).
- Bonus (indirect injection through a manager comment) not attempted.
