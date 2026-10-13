# Regression check — baseline -> mitigated

Scope: repeat 1 only; 10 runs before, 10 runs after, same cases.

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

| metric | before | after |
|---|---|---|
| outcome_pass_rate | 100.0% | 100.0% |
| trajectory_pass_rate | 90.0% | 100.0% |
| gap | +0.100 | +0.000 |
| tool_choice_accuracy | 90.0% | 100.0% |
| argument_validity | 100.0% | 100.0% |
| step_efficiency_mean | 1.07 | 1.10 |
| step_efficiency_max | 1.50 | 1.50 |
| cost_p50_usd | $0.000196 | $0.000238 |
| cost_max_usd | $0.000320 | $0.000381 |
| cost_mean_usd | $0.000234 | $0.000252 |
| tokens_p50 | 2152 | 2678 |
| tokens_max | 3436 | 4231 |
| latency_p50_s | 2.35 | 2.49 |
| latency_max_s | 2.84 | 10.46 |
