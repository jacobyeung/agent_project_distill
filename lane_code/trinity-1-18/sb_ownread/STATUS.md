# sb_ownread STATUS

- Stage 0 (survey) done 04:30Z on trinity-1-18.
- Stage 1 (build) done 04:40Z. `kit/build_ownread.py` null fork reproduces A4 `1.tgz` dcff1068… (15/15 members).
- Stage 2 (scorer) done 04:45Z. `kit/ownread.py` reproduces the registered step-544 gaps from reference rows (−35.13/−19.33/−32.87; the 544-RNG intervals equal the registered ones).
- Stage 3 (CPU proof) done 04:50Z. `kit/tests/cpu_proof.py` passed (rehearsal entry, settings identity against A4, fixture read 900/900 through the real operator, runner and launch.run, real unpack_return, strict and fixture scoring).
- Stage 4 (operator note, final build, report, tar) done 05:00Z. Final proof build `out/pkg/b200`: token ade90fc02479b, delivery af37ab141f6d0304264ffdeb47ec840037fce6366b5825f5c7142508b16147bf, plan e89dfe56…, builder da36573a….
- Stage 5 (review fixes, task sb_ownfix) done 05:31Z. The independent review (`sb_owrev/REVIEW_VERDICT.md`) returned GO AFTER FIXES. `kit/ownread.py` (now 341477c6…) refuses an incomplete paired set by default, with exit 2 and a one-line reason; `--allow-partial` marks every line PARTIAL and withholds the decision. It also checks the EXPORT_PIN archive sha256 against `READ_PLAN.export_binding.archive_sha256`, ties INPUTS to IDENTITY and the plan's archive, and requires each journal's binding ids, shard and directory to match its planned type members, refusing rows outside them. Package bytes are unchanged (no reseal). On b200, `cpu_proof.py` passed with a new partial-return step (`work/proofc`), 51/51 tests passed (29 new; all 29 fail on the reviewed scorer) and `check_build.py` passed. A copy of the reviewer's probe (`work/probe_fix`) refuses all five mutations.
- Deliverables: `out/OWNREAD_REPORT.md` (with a Review fixes section), `kit/OPERATOR.md`, `out/DESIGN_RECORD_DRAFT.md`, and `out/sb_ownread_kit.tar` with sha256 3e91dbfae5c605c7faafac6046f71095fd9aa28be58d13a4ec96a94e771840ec (`out/sb_ownread_kit.tar.sha256`, 1106 members). The extracted tar passes `check_build.py` and 51/51 tests, and rescoring reproduces the proof scores (`work/tarcheck3`). The reviewed tar ac9373ee… is kept as `work/sb_ownread_kit_reviewed_ac9373ee.tar`.
- Task complete; nothing launched.

## Decisions
- Fork = A4 delivery with a new token, a new operator `a/6.py` (bundled as `7.py` in `BATCH.sh`), and payload bytes unchanged except `9.json` token. Reason: the payload's per-type `run()` path already serves `--arms tower,own`; only the single-worker `run_types` path refuses two arms. No payload change keeps reader/evaluator/maker/parity hashes equal to A4's.
- Read = camera types 0,1,2 (450 items) x arms tower,own x mode none = 900 reads, one read descriptor, per-type worker processes.
- Own scale rule: encoded in code only (`h1eval/perception.py` OwnPerception, scale one), identical to the H1-0 kit; no settings knob.
- 1 GPU, 05:00:00: `unpack_return.py` refuses `cards != 1`; estimate 2.1 h.
- Archives sealed with out3's `tarbytes` in GNU format (the Python 3.6 default that sealed A4).
- Primary interval `score_r5.bootstrap`; the registered 544 intervals came from `h1eval.statistics.bootstrap` (seed 20261115), printed beside it.
- Within-5 bar reported two ways: point ≥ −5 and 95% lower bound > −5 (tower_pair's takeover bar); OPERATOR.md recommends the interval form.
- Journal contract mirrors the payload's `h1eval/h10/merge.py`: declared ids equal the type-and-card members in manifest order, and rows lie inside them. Under `--allow-partial` the ids checks still apply; only completeness relaxes.

## Superseded, left in place (deletion is the user's call)
- `out/pkg/p200`, `out/pkg/r200`: earlier builds of the same token and the same `1.tgz`; excluded from the kit.
- `work/proof`, `work/proof1`–`proof4`, `work/proofb`, `work/pytest_tmp/*`, `work/ob_*`, `work/tarcheck*`, `work/oldkit_check`, `work/fix`, `work/probe_fix/work`: debugging and check runs.
- `work/sb_ownread_kit_reviewed_ac9373ee.tar`: the reviewed kit tar.
- `out/OPERATOR_DIFF_VS_A4.patch`: duplicate of `kit/OPERATOR_DIFF_VS_A4.patch`.

## Pending for the user or orchestrator
- File `out/DESIGN_RECORD_DRAFT.md` under `/data2/jjyeung/agent_project_data/distill_design/` (this task permitted workspace writes only).
- GO before any launch (see `kit/OPERATOR.md`); the orchestrator decides whether the reviewer confirms the two fixes.
