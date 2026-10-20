# Requirements: the product notebooks

EARS (Mavin et al., RE'09, doi:10.1109/RE.2009.9). Every requirement names the gate that fails when it is violated.
The notebooks are the product's didactic layer (CAOS_MANAGE `conventions/product-notebooks.md`, Felipe 2026-10-20): the
folder `notebooks/` holds two trees, `en/` and `es/`, with the same notebooks at the same relative paths, by topic and from
simple to complex (level 1 fundamentals, 2 the method in practice, 3 state of the art, 4 beyond it). They import the
product's methods and never re-implement them. The static check is `scripts/check_notebooks.py` (CI and local); the
execution is `scripts/run_notebooks.py --check`, a local release gate that never runs in CI (ADR-0074). The guide is
[`docs/guides/08_notebooks.md`](../../../guides/08_notebooks.md).

| ID | Requirement | Gate |
|---|---|---|
| NB-001 | THE notebooks folder SHALL hold `README.md`, `requirements.txt`, `en/README.md` and `es/README.md`, and each topic folder SHALL hold only notebooks. | `tests/test_check_notebooks.py::test_missing_layout_files_are_found` |
| NB-002 | THE two language trees SHALL hold the same relative paths. | `tests/test_check_notebooks.py::test_a_path_missing_from_one_tree_is_found` |
| NB-003 | THE topics and the notebooks SHALL be numbered with two digits, contiguous from 01. | `tests/test_check_notebooks.py::test_numbering_gap_is_found` |
| NB-004 | THE level of a notebook SHALL never be lower than the level of the notebook before it in its topic. | `tests/test_check_notebooks.py::test_a_decreasing_level_is_found` |
| NB-005 | EVERY topic SHALL have a level 1 and a level 2 notebook. | `tests/test_check_notebooks.py::test_a_topic_without_level_two_is_found` |
| NB-006 | IF a topic has no level 3 notebook, THEN its row of each language's index SHALL give the reason. | `tests/test_check_notebooks.py::test_a_topic_without_level_three_needs_a_reason` |
| NB-007 | EACH language's index SHALL list every notebook of its tree. | `tests/test_check_notebooks.py::test_an_unlisted_notebook_is_found` |
| NB-008 | EVERY claim of the SDD section Beyond the state of the art SHALL be covered by a level 4 notebook in each language, and a notebook SHALL claim only what the SDD lists. | `tests/test_check_notebooks.py::test_an_uncovered_claim_is_found` |
| NB-009 | EACH notebook SHALL carry the second-level sections its level requires, in its tree's language and in order. | `tests/test_check_notebooks.py::test_a_missing_and_a_misordered_section_are_found` |
| NB-010 | THE first cell of a notebook SHALL be a markdown cell. | `tests/test_check_notebooks.py::test_a_first_cell_that_is_code_is_found` |
| NB-011 | EVERY code cell SHALL be directly preceded by a markdown cell and SHALL carry a comment line. | `tests/test_check_notebooks.py::test_a_code_cell_without_comment_or_explanation_is_found` |
| NB-012 | THE caos metadata of a notebook SHALL agree with its tree, its folder, the pins of `notebooks/requirements.txt` and the repository's files. | `tests/test_check_notebooks.py::test_the_caos_block_must_agree_with_the_repository` |
| NB-013 | THE notebook metadata SHALL hold only kernelspec, language_info and caos, and a cell's metadata only tags. | `tests/test_check_notebooks.py::test_extra_metadata_is_found` |
| NB-014 | THE execution counts of a notebook SHALL run 1, 2, 3 in order. | `tests/test_check_notebooks.py::test_execution_counts_must_run_in_order` |
| NB-015 | NO notebook SHALL hold an error output or a stderr stream. | `tests/test_check_notebooks.py::test_an_error_output_and_a_stderr_stream_are_found` |
| NB-016 | NO cell or output SHALL hold an absolute or machine path or a token. | `tests/test_check_notebooks.py::test_a_machine_path_and_a_token_are_found` |
| NB-017 | A notebook SHALL stay within the size limit of a notebook and each image within the limit of an image. | `tests/test_check_notebooks.py::test_oversize_notebook_and_image_are_found` |
| NB-018 | A notebook and its counterpart in the other language SHALL carry the same level, packages, data and beyond claims and the same sequence of cell kinds. | `tests/test_check_notebooks.py::test_a_spanish_notebook_that_is_not_a_counterpart_is_found` |
| NB-019 | NO notebook SHALL define a function or a class that the pipeline's engine or oracle modules already define. | `tests/test_check_notebooks.py::test_a_notebook_that_redefines_the_engine_is_found` |
| NB-020 | THE CI SHALL run `check_notebooks.py` and `check_readme_areas.py` and SHALL never execute the notebooks. | `tests/test_check_notebooks.py::test_ci_must_run_the_static_checks_and_never_the_notebooks` |
| NB-021 | THE pins of `notebooks/requirements.txt` SHALL be exact and SHALL be rows of the SDD technology table. | `tests/test_check_notebooks.py::test_notebook_pins_are_exact_and_in_the_sdd_table` |
| NB-022 | THE runner SHALL execute each notebook top to bottom in a fresh kernel, write it in place without volatile metadata, and in check mode write nothing. | `tests/test_check_notebooks.py::test_the_runner_strips_volatile_metadata` |
| NB-023 | IF a notebook raises, THEN THE runner SHALL fail naming the notebook and the error, and SHALL not rewrite the notebook. | `tests/test_check_notebooks.py::test_the_runner_fails_a_raising_notebook_naming_it` |
| NB-024 | IF an artifact a notebook reads is missing, THEN THE run SHALL fail with the artifact's path and nothing SHALL stand in for it. | `tests/test_check_notebooks.py::test_the_runner_fails_a_missing_artifact_naming_its_path` |
| NB-025 | EVERY source a notebook names in its metadata SHALL be a source the SDD lists. | `tests/test_check_notebooks.py::test_a_source_the_sdd_does_not_list_is_found` |
| NB-026 | THE committed example set SHALL pass the static check in both languages, with a level 3 notebook, and every example notebook SHALL import the engine from the pipeline. | `tests/test_check_notebooks.py::test_the_committed_set_covers_both_languages_and_a_level_three` |
| NB-027 | THE example notebooks SHALL be listed by the residue guard in a product that still holds them. | `tests/test_check_notebooks.py::test_the_residue_guard_lists_the_example_notebooks` |
| NB-028 | EVERY package of a notebook's `caos.packages` SHALL be an exact line of `notebooks/requirements.txt`, `name==version` or `name @ git+https://github.com/<owner>/<repo>.git@<tag>`, and WHERE it is installed from its release tag THE Setup section SHALL hold the sentence "not yet published on PyPI; installed from its release tag". | `tests/test_check_notebooks.py::test_a_package_installed_from_its_release_tag_passes_in_its_exact_form` |
| NB-029 | A notebook SHALL never run `pip` or `conda`; THE Setup section shows the install command. | `tests/test_check_notebooks.py::test_a_notebook_never_runs_pip` |
| NB-030 | NO cell or output SHALL hold a drive path in any literal form (a slash, one or two backslashes) or an absolute POSIX root (`/opt/`, `/tmp/`, `/root/`, `/var/`, `/srv/`). | `tests/test_check_notebooks.py::test_a_drive_path_literal_and_the_posix_roots_are_found` |
| NB-031 | NO output SHALL print a traceback to stdout. | `tests/test_check_notebooks.py::test_a_traceback_printed_to_stdout_is_found` |
| NB-032 | EVERY notebook SHALL live at `notebooks/<language>/<topic>/<notebook>.ipynb`. | `tests/test_check_notebooks.py::test_a_notebook_outside_the_layout_is_found` |
| NB-033 | THE Setup section SHALL show a `pip install` line for each package of the notebook, and THE References section SHALL list every link of `caos.sources`. | `tests/test_check_notebooks.py::test_the_install_line_and_the_references_are_enforced` |
| NB-034 | THE runner SHALL write consecutive stream outputs of one name as one output, so that two runs write the same bytes. | `tests/test_check_notebooks.py::test_consecutive_streams_of_one_name_are_coalesced` |
| NB-035 | IF the committed bytes of a notebook differ from a fresh run, THEN `run_notebooks.py --check` SHALL fail naming the notebook as stale. | `tests/test_check_notebooks.py::test_check_fails_a_notebook_whose_committed_outputs_are_stale` |
| NB-036 | IF a notebook is outside the layout, THEN THE runner SHALL fail naming it before it executes any notebook. | `tests/test_check_notebooks.py::test_the_runner_refuses_a_notebook_outside_the_layout_and_runs_none` |
| NB-037 | THE final-size oracle (`data-pipeline/pipeline/oracles.py`) SHALL solve `z = 1 - exp(-R0 z)` and `1 - z = (1 - i0) exp(-R0 z)` and SHALL share no code with the engine. | `tests/test_oracles.py::test_the_solution_satisfies_the_final_size_relation` |
| NB-038 | THE example notebooks SHALL import the final-size oracle from the pipeline and SHALL define none of their own. | `tests/test_check_notebooks.py::test_the_final_size_solver_is_imported_by_the_notebooks_and_defined_in_none` |
| NB-039 | THE content-standards guard SHALL scan the notebooks (`.ipynb`) for an em-dash or an emoji. | `tests/adversarial/test_notebooks_refuted.py::test_an_ipynb_with_an_em_dash_or_an_emoji_is_found_by_the_content_standards` |
| NB-040 | THE convergence cell of the level 2 notebook SHALL run the case its figure names (EX02_epidemic) by binding it itself. | `tests/test_check_notebooks.py::test_the_convergence_cell_names_the_case_it_runs` |
