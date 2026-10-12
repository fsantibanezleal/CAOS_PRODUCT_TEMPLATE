# Adversarial validation: the web product's problem context and documentation

For each requirement of [`requirements.md`](requirements.md), the check that tries to break it: what was planted or
refuted, and the test that plants it. `scripts/check_sdd.py` fails when a requirement has no row here (or two), when a
check is empty, and when a gate names a test that does not exist.

| requirement | adversarial check | gate |
|---|---|---|
| WB-001 | the brief removed from a copy of the real SDD, then moved to the end, then one part emptied: each makes the guard fail naming the brief, its place or the part | `tests/adversarial/test_guards_reject_planted_defects.py::test_sdd_the_executive_brief_removed` |
| WB-002 | the Initiative rewritten with "significant" and "many" in place of numbers, and a source path that is not in the repository: both are refused | `tests/adversarial/test_guards_reject_planted_defects.py::test_sdd_the_initiative_stripped_of_its_numbers` |
| WB-003 | the Outcomes table cut to two rows in a copy of the real SDD; and a proof point citing a file that is not there | `tests/adversarial/test_guards_reject_planted_defects.py::test_sdd_the_outcomes_cut_to_two_rows` |
| WB-004 | three positioning bullets, two answered questions and an equation (`$...$`) planted one at a time in a copy of the real SDD | `tests/adversarial/test_guards_reject_planted_defects.py::test_sdd_an_equation_planted_in_the_brief` |
