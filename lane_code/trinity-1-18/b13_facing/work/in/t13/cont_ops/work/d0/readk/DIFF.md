# Source classification

Baseline: the authenticated evalx27 package `f42aa1a4`. The production wrapper imports the accepted runtime direct reader, checks its SHA256, and requires the accepted `d27804f7…` evaluator source digest. It does not execute the package’s optional official-data filter.

`direct.py`, `common.py`, `export_check.py`, and the r3/r4/r5 adapters retain their package bytes. The bind fixtures also compare all four prompt inventories to the accepted packet. The full archive-admission function and room-bootstrap function have identical ASTs to their reviewed sources.

Every added, removed, or replaced line is covered below. BEYOND is conservative: it includes all control-flow, admission, selection, packaging, documentation, and omitted official-workflow lines. PATH/ENV covers only the return alias/schema substitutions. Omitted files are absent from this specialized package, not removed from any source directory.

R1 is the primary agent’s completed local code review in `REVIEW.md`; it is not an independent review. Exact hunks are in `evidence/SOURCE.patch`; hashes and ranges are in `evidence/SOURCE_DIFF.json`.

| File | Baseline lines | Candidate lines | Class | Review |
|---|---:|---:|---|---|
| `PROOF_JOB.md` | 1–98 | — | BEYOND | R1 |
| `build/ORIGINS.json` | 1–74 | — | BEYOND | R1 |
| `build/PASS2_FILES.json` | 1–674 | — | BEYOND | R1 |
| `build/coverage_report.py` | 1–67 | — | BEYOND | R1 |
| `build/package.py` | 1–71 | — | BEYOND | R1 |
| `build/phase_b_reference.py` | 1–39 | — | BEYOND | R1 |
| `cohort/COHORT_OFFICIAL6.jsonl` | 1–4008 | — | BEYOND | R1 |
| `cohort/MEDIA_MANIFEST.json` | 1–1442 | — | BEYOND | R1 |
| `cohort/frame_plan.py` | 1–80 | — | BEYOND | R1 |
| `cohort/meta_5130.jsonl` | 1–5130 | — | BEYOND | R1 |
| `launcher/chain_save.py` | 79–98 | 79–86 | BEYOND | R1 |
| `launcher/chain_save.py` | 100–109 | 88–92 | BEYOND | R1 |
| `launcher/chain_save.py` | 131 | 114 | BEYOND | R1 |
| `launcher/export_stage.py` | — | 1–224 | BEYOND | R1 |
| `launcher/orchard_job.py` | 134 | 134 | BEYOND | R1 |
| `launcher/orchard_job.py` | 137–140 | — | BEYOND | R1 |
| `launcher/orchard_job.py` | 264 | 260 | BEYOND | R1 |
| `launcher/orchard_job.py` | 269 | 265 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 23 | 23 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 36 | 36 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 59 | 59 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 85 | 85 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 105 | 105 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 144–146 | 144 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 148 | 146 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 150 | 148 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 152–153 | 150–159 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 168–169 | 174 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 171–220 | 176–207 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 222–227 | 209–215 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 229–230 | 217–218 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 232–233 | 220–226 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 387–389 | 380–382 | BEYOND | R1 |
| `launcher/orchard_launcher.py` | 400 | 393 | BEYOND | R1 |
| `launcher/orchard_results.py` | 14–15 | 14–15 | PATH/ENV | R1 |
| `launcher/orchard_results.py` | 107 | 107 | PATH/ENV | R1 |
| `launcher/orchard_results.py` | 167 | 167 | PATH/ENV | R1 |
| `launcher/orchard_stage.py` | — | 232 | BEYOND | R1 |
| `launcher/orchard_stage.py` | — | 238 | BEYOND | R1 |
| `launcher/orchard_stage.py` | 265–295 | 267–269 | BEYOND | R1 |
| `launcher/return_io.py` | 1 | 1 | BEYOND | R1 |
| `launcher/return_io.py` | 48–49 | 48 | BEYOND | R1 |
| `parity/ACCEPTED20.json` | 1–82 | — | BEYOND | R1 |
| `parity/DEV20.json` | 1 | — | BEYOND | R1 |
| `parity/PROMPT_PINS.json` | 1–1527 | — | BEYOND | R1 |
| `parity/prove_prompts.py` | 1–51 | — | BEYOND | R1 |
| `proof/COVERAGE.json` | 1 | — | BEYOND | R1 |
| `proof/COVERAGE_SUMMARY.json` | 1–6 | — | BEYOND | R1 |
| `proof/LINES.md` | 1–639 | — | BEYOND | R1 |
| `proof/LINES_CHECK.json` | 1–11699 | — | BEYOND | R1 |
| `proof/LINES_LOCAL.json` | 1–11699 | — | BEYOND | R1 |
| `proof/LOCAL_LINES.json.gz` | binary: 5890 bytes | binary: 0 bytes | BEYOND | R1 |
| `proof/PROOF.md` | 1–21 | — | BEYOND | R1 |
| `proof/SCORER_CHECK.json` | 1–74 | — | BEYOND | R1 |
| `proof/coverage.ini` | 1–14 | — | BEYOND | R1 |
| `proof/fakes.py` | 1–138 | — | BEYOND | R1 |
| `proof/fixtures.py` | 1–61 | — | BEYOND | R1 |
| `proof/lines_report.py` | 1–134 | — | BEYOND | R1 |
| `proof/measure.py` | 1–29 | — | BEYOND | R1 |
| `proof/orchard_env.py` | 1–4 | — | BEYOND | R1 |
| `proof/plan_on_orchard.py` | 1–27 | — | BEYOND | R1 |
| `proof/run.py` | 1–213 | — | BEYOND | R1 |
| `proof/run_on_orchard.sh` | 1–4 | — | BEYOND | R1 |
| `proof/runtime_checks.py` | 1–26 | — | BEYOND | R1 |
| `proof/selection.py` | 1–38 | — | BEYOND | R1 |
| `reader/PROTOCOL.json` | — | 1–204 | BEYOND | R1 |
| `reader/chain.py` | 1 | 1 | BEYOND | R1 |
| `reader/chain.py` | 3 | — | BEYOND | R1 |
| `reader/chain.py` | 10–13 | — | BEYOND | R1 |
| `reader/chain.py` | 15–21 | 10–13 | BEYOND | R1 |
| `reader/chain.py` | 25–48 | 17–22 | BEYOND | R1 |
| `reader/chain.py` | 50–98 | 24–52 | BEYOND | R1 |
| `reader/chain.py` | 102–104 | 56–58 | BEYOND | R1 |
| `reader/e193_contract.json` | — | 1–248 | BEYOND | R1 |
| `reader/e193_items.json` | — | 1–2368 | BEYOND | R1 |
| `reader/paired_read.py` | — | 1–144 | BEYOND | R1 |
| `reader/records.py` | — | 1–54 | BEYOND | R1 |
| `reader/trinity_read.py` | — | 1–22 | BEYOND | R1 |
| `reader/worker.py` | — | 1–111 | BEYOND | R1 |
| `tests/conftest.py` | 1–6 | — | BEYOND | R1 |
| `tests/test_kit.py` | 1–237 | — | BEYOND | R1 |
| `tests/test_pass2.py` | 1–257 | — | BEYOND | R1 |
| `tests/test_pass3.py` | 1–252 | — | BEYOND | R1 |

The following Trinity-side additions are BEYOND in their entirety and are included in R1:
- `f1f2.py`: lines 1–210.
- `room_bootstrap.py`: lines 1–26.
- `build_review.py`: lines 1–66.
- `REPORT.md`: lines 1–49.
- `REVIEW.md`: lines 1–44.
- `FIX1.md`: lines 1–17.
- `FIX2.md`: lines 1–27.
- `tests/bind_fixture.py`: lines 1–29.
- `tests/offline_guard.py`: lines 1–19.
- `tests/test_chain.py`: lines 1–53.
- `tests/test_kit.py`: lines 1–292.
- `tests/test_verdict.py`: lines 1–318.
