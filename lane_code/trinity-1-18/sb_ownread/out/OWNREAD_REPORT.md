# OWNREAD report: tower-and-own camera read kit (not launched)

The kit is ready. At step 400 or 600, the operator writes a pin file from the export receipt, runs `build_ownread.py` and `check_build.py`, and submits one H100 job for about 2.1 h (5 h wall time). The fork reads the 450 dev-S1 camera items with arms tower and own in one job. Its tower arm's settings and every payload code byte equal A4's. The step-200 build `out/pkg/b200` proves the kit and is not for launch.

## Diff against A4 by file (delivery `1.tgz`, 15 members)

| Member | A4 sha256 | Fork sha256 | Change |
|---|---|---|---|
| `a/6.py` (operator) | 97c8e6dfe33e… | 927f6d849255… | two-arm camera read (below) |
| `BATCH.sh` | cda29adeea5a… | b58012c40953… | rebundled `{0.py, 0.json, 7.py=a/6.py}`, new token |
| `0.json`, `CONFIG.json` | d9594d3c7dc0… | 3fa237d1cd09… | token, payload sha, plan sha |
| `0.tgz` (payload, 927 files) | 4498fca72a8e… | 590eafb024d6… | only `9.json` changes: token d60a20ec01296 → ade90fc02479b |
| `PACKAGE.json` | d9eeb1875e8b… | 47fc39038204… | token and refreshed file hashes |
| `3.py`, `SUBMIT.cmd`, `INPUTS.example.json`, `a/0.json`, `a/1.json`, `a/4.py`, `a/5.py`, `a/7.py`, `a/export.json` | — | — | byte-identical |

At 400/600 the re-pin also changes `a/4.py` (its three `REVIEWED_*` constants) and `9.json` `export_binding` (step, member directory, object). `test_repin_400` checks that nothing else moves.

The operator diff (`kit/OPERATOR_DIFF_VS_A4.patch`, +34/−18) does six things:
- schedules types 0, 1, 2 (A4: 3, 0, 1, 2, 4);
- sets one descriptor to `arms=['tower','own']` and expects 900 reads (A4: tower, 636);
- runs per-type workers, `single_worker` False;
- makes the rehearsal check each type's worker arguments (`--arms tower,own`, `--types <kind>`, `--out journals/<t>/0`);
- serves the own arm's move and turn routes through the real `perception_factory` with stub heads (scale 1);
- totals 900 reads.

The memo, the rule (`candidates_argmax`), `save_own_depth`, the margins and the tower socket rehearsal are unchanged.

The Orchard scripts `o_*.sh` derive from A's templates, with each substitution count-checked:
- token, `1.tgz` checksum, object, receipt path, size and sha, and lineage/step;
- the resume part size; `o_pullfill_resume.sh` is omitted when the pin lacks `part_bytes`;
- removal of A's unrelated B-package check.

## Seal and hashes

The builder reuses out3's recipe (`rebuild.py`/`seal_delivery.py`: gzip mtime 0, sorted members, mode 0600, GNU tar). It never edits a hash by hand: its null fork reseals A4 with A4's token and operator, and must reproduce A4's `1.tgz` dcff1068… (15/15 members) before it writes anything.

| Artifact | sha256 |
|---|---|
| `out/pkg/b200/1.tgz` (token ade90fc02479b, job name `a15_cot_apade90fc02479b`) | af37ab141f6d0304264ffdeb47ec840037fce6366b5825f5c7142508b16147bf |
| plan (`9.json` canonical) | e89dfe5659fa7555b4b7503332d3d163fbd59869e65c87eb4f7132272bfea351 |
| `READ_PLAN.json` / `BUILD.json` | 0fd714f30e03d77c… / d0166885d458c96e… |
| `kit/build_ownread.py` / `kit/ownread_sequence.py` | da36573abe0436f7… / 927f6d849255bbe3… |
| `kit/ownread.py` | 12c92461a2692b04… |
| vendored `score_r5.py` / `tower_pair.py` (byte copies, pinned in `ownread.py`) | 476315803c3c995e… / ea0ae8eb4a548213… |
| refs `tower200` / `tower544` / `own544` (450 rows each) | d0d2c6ed7bcd18b4… / 00df5a4da9db65f3… / 8e150efdbb530118… |

## Tests and output (CPU, trinity-1-18, Python 3.12; helpers compiled under 3.6)

`kit/tests/cpu_proof.py out/pkg/b200 work/proofb` passed (`CPU_PROOF.json` 09a1a83aa672a490…) in five steps:
1. The rehearsal entry runs the real `a/5.py` on `tower_sequence.py`: per-type worker arguments for three workers, the tower socket stub, the own server stub, and a memory fit.
2. Settings identity: A4's operator and the fork write byte-identical tower settings (2c3cc6b4…), equal to A4's returned settings. Only `arms`, `single_worker` and `types` differ in the worker config.
3. The fixture read runs the real operator, runner, `launch.parser` and `launch.run` with a replay maker: 900/900 reads, 150 tower and 150 own per type.
4. The real `unpack_return.py` unpacks the fixture return, which `ownread --fixture` scores; strict mode refuses it ("Journal binding differs: fixture").
5. A strict return, built from A4's journal environment with both arms, scores strictly.

Strict synthetic output (tower rows = A4's step-200 return, own rows = step-544 own; this is a check of the plumbing, not a measurement):

| Type | own | tower | own−tower [95%] | 544-RNG 95% |
|---|---|---|---|---|
| displacement | 47.20 | 81.87 | −34.67 [−42.59, −26.60] | [−42.70, −26.84] |
| movement direction | 75.33 | 94.67 | −19.33 [−27.59, −11.81] | [−27.48, −11.89] |
| rotation | 42.73 | 76.27 | −33.53 [−40.13, −27.06] | [−40.15, −27.11] |

The scorer recomputes the registered step-544 gaps from the reference rows (−35.13, −19.33, −32.87). Its 544-RNG intervals equal the registered ones, and tower−tower200 is 0 with zero width.

`pytest tests/test_kit.py`: 23 passed. The suite covers:
- the null fork; re-pinning to A4's own values (byte-exact) and to a synthetic step-400 pin;
- six pin-validation refusals; `bash -n` and 3.6 heredoc compiles;
- the operator diff; ported `verify_delivery` checks;
- `check_build` on b200; camera item order equal to A4's; vendor and reference shas;
- a partial return (verdict None); five scorer refusals (duplicate, wrong arm, uncommitted tail, settings, arms).

`tests/check_build.py out/pkg/b200` passed.

## Estimated GPU time (`kit/TIME_ESTIMATE.json`)

The estimate comes from A4's and H1-0's measured read times:
- staging 257 s, then three type processes, each charged a tower load (75 s) and the largest own process overhead (113 s, own load included);
- tower decoding max(3553 s at step 200, 3448 s at step 544) plus own decoding 3139 s, then a 120 s return.

Total: 7633 s = 2.12 h on one H100. If decoding runs 1.5x slower, the job takes 3.05 h; admission stops at 4.5 h, leaving 1.48x headroom. Submit with `--gpus 1 --time 05:00:00`: about 2.1 GPU-h used and 5.0 reserved, within `3.py`'s 5 GPU-h cap. The read needs one card because `unpack_return.py` refuses returns with more than one.

## Decisions and recorded differences

- No payload change: the payload's per-type `run()` path already serves two arms, and only its single-worker path refuses own. The reader, evaluator, maker and parity hashes therefore stay equal to A4's, and `ownread.py` enforces that.
- Per-type processes keep G3T memo hits within a type (A4 shared one worker). The memo holds frozen-module values, so outputs do not change; times do, and the estimate includes them.
- The own scale rule is H1-0's (OwnPerception, scale 1). It lives in code, not settings, so the settings carry no own field. The own arm runs mode none only.
- H1-0's step-544 own rows used older reader, evaluator, maker and parity code (2c2dc559…/ad9aeb95…/44745c02…/64474315…). The deltas own−own544 therefore mix the step change with the code change; the in-read own−tower pairing does not. The step-544 tower used `null_argmax`, and A4 and the fork use `candidates_argmax`. Hence `ownread` marks step-544 deltas as "unpaired reference".
- The primary interval is `score_r5.bootstrap` (seed 17). The registered intervals came from `h1eval.statistics.bootstrap` (seed 20261115) and print beside it as "544-RNG".
- `ownread` reports two bars: point ≥ −5, and 95% lower bound > −5. `OPERATOR.md` asks that the interval bar decide whether G3T is dropped.
- Risk: no GPU has yet run this payload's per-type path with two arms; the CPU proof covers control flow, not CUDA memory or speed. If it fails, the CPU-check receipt, an incomplete `SUMMARY.json`, or a scorer refusal will show it.

## Open items for the user or orchestrator

- GO for one Orchard H100 job once the step-400 or step-600 receipt exists, plus one independent review of the operator diff and `ownread.py` (scoring code). See `kit/OPERATOR.md`.
- Confirm that the receipt path `…/gcs_673bc60f_m<step>.done` and the `q8/` object prefix hold at 400/600.
- File `out/DESIGN_RECORD_DRAFT.md` under `/data2/jjyeung/agent_project_data/distill_design/`. This task permitted writes only in its workspace.
- Superseded builds `out/pkg/p200` and `out/pkg/r200` (same `1.tgz`) and the scratch runs under `work/` remain; deleting them is the user's call.
- Kit: `out/sb_ownread_kit.tar`, with its sha256 in `out/sb_ownread_kit.tar.sha256`.
