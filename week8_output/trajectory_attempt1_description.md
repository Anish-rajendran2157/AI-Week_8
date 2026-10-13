# Trajectory eval — attempt 1 (tighter search_handbook description, REVERTED)

30 runs (10 cases x 3 repeats).

| metric | value |
|---|---|
| outcome pass rate | 86.7% |
| trajectory pass rate | 80.0% |
| **gap (outcome - trajectory)** | **+6.7 pts** |
| right answer, wrong path (runs) | 4 |
| tool-choice accuracy | 80.0% |
| argument validity | 100.0% |
| step efficiency (taken / needed), mean / max | 1.03 / 1.50 |
| cost per question p50 / max | $0.000207 / $0.000301 |
| tokens per question p50 / max | 2294 / 3410 |
| latency p50 / max (s) | 2.24 / 5.57 |

## Failure modes (runs showing each mode)

| mode | runs | meaning |
|---|---|---|
| skipped_record | 0 | answered without reading the employee record (tenure/jurisdiction guessed) |
| skipped_clause | 6 | a required handbook clause (HB-2/3/4/6) was never retrieved; formula assumed |
| wrong_argument | 0 | real but wrong arguments, e.g. the IN table for a UK transfer, another employee |
| invented_argument | 0 | an argument that does not exist: unknown employee id, non-enum value, fictional section/rule id in a query or in the final citation |
| unsupported_citation | 0 | final rule_id is real but never appeared in any tool result of the run |
| redundant_call | 0 | duplicate call, or a call outside every accepted path |
| order_violation | 0 | right calls, but in an order no accepted path allows |
| no_answer | 2 | budget fired, error, or output broke the contract |
| wrong_answer | 2 | final value does not match the expected value (outcome failure) |

## Runs

| case | outcome | trajectory | value | rule | steps | cost | modes | path |
|---|---|---|---|---|---|---|---|---|
| C01 | PASS | PASS | 5.0 | US-SL-1 | 2/2 | $0.000206 | - | get_employee_record({"employee_id":"E106"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"sick_leave"}) |
| C01 | PASS | PASS | 5.0 | US-SL-1 | 2/2 | $0.000206 | - | get_employee_record({"employee_id":"E106"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"sick_leave"}) |
| C01 | PASS | PASS | 5.0 | US-SL-1 | 2/2 | $0.000206 | - | get_employee_record({"employee_id":"E106"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"sick_leave"}) |
| C02 | PASS | PASS | 30.0 | IN-NP-2 | 3/2 | $0.000295 | - | get_employee_record({"employee_id":"E101"}) → search_handbook({"query":"notice period"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"notice_period"}) |
| C02 | PASS | PASS | 30.0 | IN-NP-2 | 3/2 | $0.000295 | - | get_employee_record({"employee_id":"E101"}) → search_handbook({"query":"notice period"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"notice_period"}) |
| C02 | PASS | PASS | 30.0 | IN-NP-2 | 3/2 | $0.000295 | - | get_employee_record({"employee_id":"E101"}) → search_handbook({"query":"notice period"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"notice_period"}) |
| C03 | PASS | PASS | 28.0 | UK-NP-1 | 2/2 | $0.000207 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C03 | PASS | PASS | 28.0 | UK-NP-1 | 2/2 | $0.000206 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C03 | PASS | PASS | 28.0 | UK-NP-1 | 2/2 | $0.000207 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C04 | PASS | FAIL | 17.0 | IN-AL-3 | 2/3 | $0.000207 | skipped_clause | get_employee_record({"employee_id":"E102"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"annual_leave"}) |
| C04 | FAIL | FAIL | None | None | 2/3 | $0.000116 | no_answer, skipped_clause | get_employee_record({"employee_id":"E102"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"annual_leave"}) |
| C04 | FAIL | FAIL | None | None | 2/3 | $0.000116 | no_answer, skipped_clause | get_employee_record({"employee_id":"E102"}) → get_jurisdiction_rules({"jurisdiction":"IN","topic":"annual_leave"}) |
| C05 | PASS | PASS | 10.0 | UK-SL-1 | 2/2 | $0.000199 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"sick_leave"}) |
| C05 | PASS | PASS | 10.0 | UK-SL-1 | 2/2 | $0.000199 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"sick_leave"}) |
| C05 | PASS | PASS | 10.0 | UK-SL-1 | 2/2 | $0.000199 | - | get_employee_record({"employee_id":"E103"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"sick_leave"}) |
| C06 | PASS | PASS | 0.0 | SG-SL-1 | 3/2 | $0.000297 | - | get_employee_record({"employee_id":"E107"}) → search_handbook({"query":"sick leave SG"}) → get_jurisdiction_rules({"jurisdiction":"SG","topic":"sick_leave"}) |
| C06 | PASS | PASS | 0.0 | SG-SL-1 | 3/2 | $0.000297 | - | get_employee_record({"employee_id":"E107"}) → search_handbook({"query":"sick leave SG"}) → get_jurisdiction_rules({"jurisdiction":"SG","topic":"sick_leave"}) |
| C06 | PASS | PASS | 0.0 | SG-SL-1 | 3/2 | $0.000297 | - | get_employee_record({"employee_id":"E107"}) → search_handbook({"query":"sick leave SG"}) → get_jurisdiction_rules({"jurisdiction":"SG","topic":"sick_leave"}) |
| C07 | PASS | PASS | 10.0 | US-AL-1 | 2/2 | $0.000206 | - | get_employee_record({"employee_id":"E105"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"annual_leave"}) |
| C07 | PASS | PASS | 10.0 | US-AL-1 | 2/2 | $0.000205 | - | get_employee_record({"employee_id":"E105"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"annual_leave"}) |
| C07 | PASS | PASS | 10.0 | US-AL-1 | 2/2 | $0.000208 | - | get_employee_record({"employee_id":"E105"}) → get_jurisdiction_rules({"jurisdiction":"US-CA","topic":"annual_leave"}) |
| C08 | FAIL | PASS | 15.0 | UK-AL-1 | 3/3 | $0.000301 | wrong_answer | get_employee_record({"employee_id":"E109"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"annual_leave"}) → search_handbook({"query":"part-time annual leave"}) |
| C08 | FAIL | PASS | 15.0 | UK-AL-1 | 3/3 | $0.000299 | wrong_answer | get_employee_record({"employee_id":"E109"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"annual_leave"}) → search_handbook({"query":"part-time annual leave"}) |
| C08 | PASS | PASS | 16.5 | UK-AL-2 | 3/3 | $0.000297 | - | get_employee_record({"employee_id":"E109"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"annual_leave"}) → search_handbook({"query":"part-time annual leave"}) |
| C09 | PASS | FAIL | 28.0 | UK-NP-2 | 2/3 | $0.000252 | skipped_clause | get_employee_record({"employee_id":"E108"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C09 | PASS | FAIL | 28.0 | UK-NP-2 | 2/3 | $0.000250 | skipped_clause | get_employee_record({"employee_id":"E108"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C09 | PASS | FAIL | 28.0 | UK-NP-2 | 2/3 | $0.000254 | skipped_clause | get_employee_record({"employee_id":"E108"}) → get_jurisdiction_rules({"jurisdiction":"UK","topic":"notice_period"}) |
| C10 | PASS | PASS | 0.0 | HB-3 | 2/2 | $0.000203 | - | get_employee_record({"employee_id":"E110"}) → search_handbook({"query":"contractor annual leave"}) |
| C10 | PASS | PASS | 0.0 | HB-3 | 2/2 | $0.000203 | - | get_employee_record({"employee_id":"E110"}) → search_handbook({"query":"contractor annual leave"}) |
| C10 | PASS | PASS | 0.0 | HB-3 | 2/2 | $0.000203 | - | get_employee_record({"employee_id":"E110"}) → search_handbook({"query":"contractor annual leave"}) |
