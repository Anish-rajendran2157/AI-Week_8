"""The 10 HR trajectory cases: expected tool sequences, with legitimate alternates accepted as a set.

A case lists its `required` steps and its `optional` steps. The accepted paths are every ordering of
the required steps plus any subset of the optional steps, filtered by `record_first`:

- record_first=True  -> get_employee_record must be the first call: the jurisdiction (and so which
                        rule table to fetch) is only known after reading the record.
- record_first=False -> the question itself names the jurisdiction, so fetching the rule table before
                        or after the record are both correct. The record is still required.

Optional steps are the alternates that are correct but not needed, e.g. one exception-check
search_handbook on a plain full-time question, or reading the SG table before discovering the
person is a contractor. A step matches a call by tool name plus the argument values that matter;
for search_handbook it matches when the call's *result* contains the required clause, because the
query is free text and many phrasings are correct.
"""
from dataclasses import dataclass, field
from itertools import combinations, permutations


@dataclass(frozen=True)
class Step:
    tool: str
    args: tuple = ()      # (name, value) pairs the call must carry, compared case-insensitively
    clause: str = None    # search_handbook only: this section (e.g. "HB-4") must be in the result

    def matches(self, call: dict) -> bool:
        if call["tool"] != self.tool or call["args"] is None:
            return False
        for name, value in self.args:
            if str(call["args"].get(name, "")).strip().upper() != value.upper():
                return False
        if self.clause:
            sections = call["result"] if isinstance(call["result"], list) else []
            return any(s["section"].split(" ")[0] == self.clause for s in sections)
        return True

    def __str__(self):
        if self.clause:
            return f"search_handbook(-> {self.clause})"
        if self.tool == "search_handbook":
            return "search_handbook(any)"
        return f"{self.tool}({', '.join(v for _, v in self.args)})"


def record(employee_id):
    return Step("get_employee_record", (("employee_id", employee_id),))


def rules(jurisdiction, topic):
    return Step("get_jurisdiction_rules", (("jurisdiction", jurisdiction), ("topic", topic)))


def clause(section):
    return Step("search_handbook", clause=section)


ANY_SEARCH = Step("search_handbook")


@dataclass
class Case:
    id: str
    question: str
    expected_value: float
    employee_id: str
    required: list
    optional: list = field(default_factory=list)
    record_first: bool = True
    note: str = ""

    def accepted_paths(self) -> set:
        paths = set()
        for k in range(len(self.optional) + 1):
            for extra in combinations(self.optional, k):
                for perm in permutations(self.required + list(extra)):
                    if self.record_first and perm[0].tool != "get_employee_record":
                        continue
                    paths.add(perm)
        return paths

    @property
    def steps_needed(self) -> int:
        return len(self.required)


CASES = [
    Case("C01", "Maria Lopez (E106) works in our California office. How many paid sick days do they get this year?",
         5, "E106", [record("E106"), rules("US-CA", "sick_leave")], [ANY_SEARCH], record_first=False,
         note="lure: jurisdiction is in the question and US-CA sick leave has one band, so the record "
              "looks skippable; it is still required (employment type could make it 0)"),
    Case("C02", "E101 wants to resign. What notice period must they give, in days?",
         30, "E101", [record("E101"), rules("IN", "notice_period")], [ANY_SEARCH],
         note="tenure branch: 18 months -> IN-NP-2"),
    Case("C03", "Oliver Grant (E103) has been in our London office for over two years. If they resign, "
                "what notice period in days applies?",
         28, "E103", [record("E103"), rules("UK", "notice_period")], [ANY_SEARCH], record_first=False,
         note="lure: the question claims 2+ years; the record says 20 months (UK-NP-1, 28 days). Trusting "
              "the question gives UK-NP-2 = max(28, 7x2) = 28 too, so the answer is right either way and "
              "only the trajectory shows whether tenure was read"),
    Case("C04", "How many annual leave days does E102 have left this year?",
         17, "E102", [record("E102"), rules("IN", "annual_leave"), clause("HB-4")],
         note="balance needs the carry-over clause HB-4 (entitlement + carry-over - taken)"),
    Case("C05", "How many paid sick days does E103 get?",
         10, "E103", [record("E103"), rules("UK", "sick_leave")], [ANY_SEARCH],
         note="tenure branch: 20 months -> UK-SL-1"),
    Case("C06", "Is E107 entitled to any paid sick leave yet? Give the number of days.",
         0, "E107", [record("E107"), rules("SG", "sick_leave")], [ANY_SEARCH],
         note="tenure branch: 4 months -> SG-SL-1 (0 days)"),
    Case("C07", "What is E105's annual leave entitlement for the year?",
         10, "E105", [record("E105"), rules("US-CA", "annual_leave")], [ANY_SEARCH],
         note="tenure branch: 7 months -> US-AL-1"),
    Case("C08", "What is E109's annual leave entitlement in days?",
         16.5, "E109", [record("E109"), rules("UK", "annual_leave"), clause("HB-6")],
         note="part-time: needs HB-6 (x FTE, round down to half day); clause and table in either order"),
    Case("C09", "E108 is relocating to the UK office on 1 November 2026. If they resign after the move, "
                "what notice period in days will apply?",
         28, "E108", [record("E108"), rules("UK", "notice_period"), clause("HB-2")],
         note="transfer: needs HB-2 and the destination (UK) table, not the record's IN table"),
    Case("C10", "How many annual leave days does E110 get?",
         0, "E110", [record("E110"), clause("HB-3")], [rules("SG", "annual_leave")],
         note="contractor: HB-3 makes it 0; reading the SG table too is a valid but unneeded alternate"),
]
