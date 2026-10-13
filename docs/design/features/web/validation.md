# Adversarial validation: the web product's problem context and documentation

For each requirement of [`requirements.md`](requirements.md), the check that tries to break it: what was planted or
refuted, and the test that plants it. `scripts/check_sdd.py` fails when a requirement has no row here (or two), when a
check is empty, and when a gate names a test that does not exist.

| requirement | adversarial check | gate |
|---|---|---|
| WB-001 | the brief removed from a copy of the real SDD, moved to the end, its data line removed, and the four old parts written back into it: each makes the guard fail naming the brief, its place, the line or the restating | `tests/adversarial/test_guards_reject_planted_defects.py::test_sdd_the_executive_brief_removed` |
| WB-002 | the real `content/executive.json` removed, then one field of it deleted and one invented, in a copy of the repository: each fails naming the file and the field path | `tests/adversarial/test_guards_reject_planted_defects.py::test_executive_view_the_data_file_removed_or_broken` |
| WB-003 | the shell's installed schema removed from a copy of the repository: the guard fails and names `npm ci` instead of passing | `tests/adversarial/test_guards_reject_planted_defects.py::test_executive_view_without_the_installed_schema` |
| WB-004 | each of the three real SVG files removed from a copy of the repository, and one replaced by an SVG with no viewBox: each fails naming its field path | `tests/adversarial/test_guards_reject_planted_defects.py::test_executive_view_a_missing_or_blank_illustration` |
| WB-005 | the source of one headline figure removed from a copy of the real file, an uncited source added, and a source link turned to http: each is refused | `tests/adversarial/test_guards_reject_planted_defects.py::test_executive_view_a_figure_without_its_source_link` |
| WB-006 | the executive tab planted second and the data file replaced by an invalid one: the page is not the executive view, or shows the error state | `frontend/src/pages/Introduction.test.tsx::adversarial: an invalid data file renders the error state and not a blank view` |
| WB-007 | a literal colour, a `data-chart` attribute and a label with no Spanish twin planted one at a time in the real illustrations; a sentence of 31 words, an uncited source, an insecure link, an unowned action, causes over 100 percent, a pitch and reversed 4 C's planted in the data | `frontend/src/content/executive.test.ts::adversarial: planted literal colours, charts, missing labels, long sentences and broken rules are refused` |
| WB-008 | the root and an unknown path rendered in a copy of the real app: neither renders the workbench | `frontend/src/App.test.tsx::adversarial: the root alone does not render the workbench` |
| WB-009 | a pitch word planted in an action and an owner that is no role planted in a copy of the real file: each fails naming its field path | `tests/adversarial/test_guards_reject_planted_defects.py::test_executive_view_a_pitch_a_client_or_an_unowned_action` |
