# Trajectory eval — mitigated (re-planning)

13 runs.

| metric | value |
|---|---|
| outcome pass rate | 100.0% |
| trajectory pass rate | 100.0% |
| **gap (outcome - trajectory)** | **+0.0 pts** |
| right answer, wrong path (runs) | 0 |
| tool-choice accuracy | 100.0% |
| argument validity | 100.0% |
| step efficiency (taken / needed), mean / max | 1.12 / 1.50 |
| cost per question p50 / max | $0.000194 / $0.000381 |
| tokens per question p50 / max | 2151 / 4231 |
| latency p50 / max (s) | 2.58 / 10.46 |

## Failure modes (runs showing each mode)

| mode | runs | meaning |
|---|---|---|
| skipped_record | 0 | answered without reading the employee record (tenure/jurisdiction guessed) |
| skipped_clause | 0 | a required handbook clause (HB-2/3/4/6) was never retrieved; formula assumed |
| wrong_argument | 0 | real but wrong arguments, e.g. the IN table for a UK transfer, another employee |
| invented_argument | 0 | an argument that does not exist: unknown employee id, non-enum value, fictional section/rule id in a query or in the final citation |
| unsupported_citation | 0 | final rule_id is real but never appeared in any tool result of the run |
| redundant_call | 0 | duplicate call, or a call outside every accepted path |
| order_violation | 0 | right calls, but in an order no accepted path allows |
| malformed_tool_call | 0 | provider rejected a tool call the model emitted (e.g. a tool name with a leaked '<|channel|>' token, HTTP 400 tool_use_failed); the run ends with no answer |
| no_answer | 0 | budget fired, other error, or output broke the contract |
| wrong_answer | 0 | final value does not match the expected value (outcome failure) |

## Runs

| case | outcome | trajectory | value | rule | steps | cost | modes | path |
|---|---|---|---|---|---|---|---|---|
| C01 | PASS | PASS | 5.0 | US-SL-1 | 2/2 | $0.000194 | - | get_employee_record({"employee_id":"E106"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"sick_leave"}) |
| C01 | PASS | PASS | 5.0 | US-SL-1 | 2/2 | $0.000194 | - | get_employee_record({"employee_id":"E106"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"sick_leave"}) |
| C02 | PASS | PASS | 30.0 | IN-NP-2 | 2/2 | $0.000193 | - | get_employee_record({"employee_id":"E101"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"notice_period"}) |
| C02 | PASS | PASS | 30.0 | IN-NP-2 | 2/2 | $0.000193 | - | get_employee_record({"employee_id":"E101"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"notice_period"}) |
| C03 | PASS | PASS | 28.0 | UK-NP-1 | 3/2 | $0.000283 | - | get_employee_record({"employee_id":"E103"}) → search_handbook({"query":"notice period UK tenure"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C03 | PASS | PASS | 28.0 | UK-NP-1 | 3/2 | $0.000283 | - | get_employee_record({"employee_id":"E103"}) → search_handbook({"query":"notice period UK tenure"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C04 | PASS | PASS | 17.0 | IN-AL-3 | 3/3 | $0.000381 | - | get_employee_record({"employee_id":"E102"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"annual_leave"}) → search_handbook({"query":"HB-4 carry-over"}) |
| C05 | PASS | PASS | 10.0 | UK-SL-1 | 3/2 | $0.000282 | - | get_employee_record({"employee_id":"E103"}) → search_handbook({"query":"UK sick leave entitlement"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"sick_leave"}) |
| C06 | PASS | PASS | 0.0 | SG-SL-1 | 2/2 | $0.000191 | - | get_employee_record({"employee_id":"E107"}) → get_jurisdiction_rules({"jurisdiction":"SG","topic":"sick_leave"}) |
| C07 | PASS | PASS | 10.0 | US-AL-1 | 2/2 | $0.000194 | - | get_employee_record({"employee_id":"E105"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"annual_leave"}) |
| C08 | PASS | PASS | 16.5 | UK-AL-2 | 3/3 | $0.000296 | - | get_employee_record({"employee_id":"E109"}) → search_handbook({"query":"part-time annual leave UK"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"annual_leave"}) |
| C09 | PASS | PASS | 28.0 | UK-NP-2 | 3/3 | $0.000319 | - | get_employee_record({"employee_id":"E108"}) → search_handbook({"query":"notice period"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C10 | PASS | PASS | 0.0 | HB-3 | 2/2 | $0.000190 | - | get_employee_record({"employee_id":"E110"}) → search_handbook({"query":"SG annual leave contractor"}) |
