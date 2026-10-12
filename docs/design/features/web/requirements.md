# Requirements: the web product's problem context and documentation

EARS (Mavin et al., RE'09, doi:10.1109/RE.2009.9). Every requirement names the gate that fails when it is violated.
This feature holds the design-document side of the problem-context rule (CAOS_MANAGE `conventions/problem-context-first.md`);
the page-side areas (ADR-0017 section 2.1) are measured by the shell's gate from shell 0.11.0 and are added here when
the template's pages adopt them.

| ID | Requirement | Gate |
|---|---|---|
| WB-001 | THE design document SHALL carry an executive brief right after the problem and non-goals, with the parts Initiative, Outcomes, Positioning and Credibility in that order, each with content. | `tests/test_spec_guards.py::test_brief_missing_section_fails_and_points_at_the_guide` (and, for the order and the empty parts, `test_brief_at_the_end_of_the_sdd_fails`, `test_brief_four_empty_headings_fail`) |
| WB-002 | THE executive brief SHALL state in its Initiative at least one quantified statement, a number with its unit and either a source that exists or an assumption with its reason. | `tests/test_spec_guards.py::test_brief_many_and_significant_and_several_are_not_numbers` |
| WB-003 | THE executive brief SHALL tie every capability of its Outcomes table, at least three, to a proof point with a number and its source or assumption. | `tests/test_spec_guards.py::test_brief_outcomes_with_two_rows_fail` |
| WB-004 | THE executive brief SHALL hold exactly four positioning bullets, at least three answered credibility questions and a Limits line, and no equation. | `tests/test_spec_guards.py::test_brief_an_equation_in_the_brief_fails` |
