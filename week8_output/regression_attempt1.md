# Regression check — baseline -> attempt1_description

Scope: all runs; 30 runs before, 30 runs after, same cases.

| failure mode | before | after | change |
|---|---|---|---|
| skipped_record | 0 | 0 | same |
| skipped_clause | 3 | 6 | **worse** |
| wrong_argument | 0 | 0 | same |
| invented_argument | 0 | 0 | same |
| unsupported_citation | 0 | 0 | same |
| redundant_call | 0 | 0 | same |
| order_violation | 0 | 0 | same |
| malformed_tool_call | 0 | 0 | same |
| no_answer | 0 | 2 | **worse** |
| wrong_answer | 0 | 2 | **worse** |

| metric | before | after |
|---|---|---|
| outcome_pass_rate | 100.0% | 86.7% |
| trajectory_pass_rate | 90.0% | 80.0% |
| gap | +0.100 | +0.067 |
| tool_choice_accuracy | 90.0% | 80.0% |
| argument_validity | 100.0% | 100.0% |
| step_efficiency_mean | 1.07 | 1.03 |
| step_efficiency_max | 1.50 | 1.50 |
| cost_p50_usd | $0.000196 | $0.000207 |
| cost_max_usd | $0.000327 | $0.000301 |
| cost_mean_usd | $0.000234 | $0.000231 |
| tokens_p50 | 2152 | 2294 |
| tokens_max | 3458 | 3410 |
| latency_p50_s | 2.37 | 2.24 |
| latency_max_s | 3.49 | 5.57 |
