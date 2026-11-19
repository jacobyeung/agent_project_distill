# sb_ownread STATUS

- Stage 0 (survey) done 04:30Z on trinity-1-18.
- Stage 1 (build) done 04:40Z. `kit/build_ownread.py` null fork reproduces A4 `1.tgz` dcff1068… (15/15 members).
- Stage 2 (scorer) done 04:45Z. `kit/ownread.py` reproduces the registered step-544 gaps from reference rows (−35.13/−19.33/−32.87; the 544-RNG intervals equal the registered ones).
- Stage 3 (CPU proof) done 04:50Z. `kit/tests/cpu_proof.py` passed (rehearsal entry, settings identity against A4, fixture read 900/900 through the real operator, runner and launch.run, real unpack_return, strict and fixture scoring).
- Stage 4 (operator note, final build, report, tar) done 05:00Z. Final proof build `out/pkg/b200`: token ade90fc02479b, delivery af37ab141f6d0304264ffdeb47ec840037fce6366b5825f5c7142508b16147bf, plan e89dfe56…, builder da36573a…. On b200, `cpu_proof.py` passed (`work/proofb`), 23/23 tests passed and `check_build.py` passed.
- Deliverables: `out/OWNREAD_REPORT.md` (99 lines), `kit/OPERATOR.md`, `out/DESIGN_RECORD_DRAFT.md`, and `out/sb_ownread_kit.tar` with sha256 ac9373eef3e0a55886fc182f31529f57771da1357ca2d89d8668ecdfb11de306 (`out/sb_ownread_kit.tar.sha256`). The extracted tar passes `check_build.py` and rescoring reproduces the proof scores.
- Task complete; nothing launched.

## Decisions
- Fork = A4 delivery with a new token, a new operator `a/6.py` (bundled as `7.py` in `BATCH.sh`), and payload bytes unchanged except `9.json` token. Reason: the payload's per-type `run()` path already serves `--arms tower,own`; only the single-worker `run_types` path refuses two arms. No payload change keeps reader/evaluator/maker/parity hashes equal to A4's.
- Read = camera types 0,1,2 (450 items) x arms tower,own x mode none = 900 reads, one read descriptor, per-type worker processes.
- Own scale rule: encoded in code only (`h1eval/perception.py` OwnPerception, scale one), identical to the H1-0 kit; no settings knob.
- 1 GPU, 05:00:00: `unpack_return.py` refuses `cards != 1`; estimate 2.1 h.
- Archives sealed with out3's `tarbytes` in GNU format (the Python 3.6 default that sealed A4).
- Primary interval `score_r5.bootstrap`; the registered 544 intervals came from `h1eval.statistics.bootstrap` (seed 20261115), printed beside it.
- Within-5 bar reported two ways: point ≥ −5 and 95% lower bound > −5 (tower_pair's takeover bar); OPERATOR.md recommends the interval form.

## Superseded, left in place (deletion is the user's call)
- `out/pkg/p200`, `out/pkg/r200`: earlier builds of the same token and the same `1.tgz`; excluded from the kit.
- `work/proof`, `work/proof1`–`proof4`, `work/pytest_tmp/*`, `work/ob_*`, `work/tarcheck*`: debugging and check runs.
- `out/OPERATOR_DIFF_VS_A4.patch`: duplicate of `kit/OPERATOR_DIFF_VS_A4.patch`.

## Pending for the user or orchestrator
- File `out/DESIGN_RECORD_DRAFT.md` under `/data2/jjyeung/agent_project_data/distill_design/` (this task permitted workspace writes only).
- GO and one independent review before any launch (see `kit/OPERATOR.md`).
