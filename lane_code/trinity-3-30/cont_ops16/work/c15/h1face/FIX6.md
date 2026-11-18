# R1 direct reads

The launcher admits run `673bc60f` from deployment `x_69d2930d` and continuation `05b8ac69` from `x_7f1589c1`, both in namespace `8865619b`. Each accepts `main`, `a7`, or both, with `--types direct` or without a filter. Run `469ddece` remains restricted to `a7`, generation `mstop`, step 544.

| Run | Milestones | Claimed generations | Actual stop steps |
|---|---|---|---|
| `673bc60f` | 100, 200 | mstop, mstopB, mstopC | 1–200 |
| `05b8ac69` | 400, 600 | mstop, mstopB, mstopC | 201–600 |

Only three previously pinned kit files change. All **74 reader files** match FIX5 FINAL_PINS `f8911c19041a6bdb3bdf4734e2841a96fd7364675f202ddd0efabc5bc0d9203a`, including the five files that the registration permits to change. No evaluator, scorer, adapter, reader, asset or production build file was edited. The registration's closing sentence says 72 reader files; the authenticated inventory contains 74, and the test compares every one.

## Changed lines

| File | Lines | Change |
|---|---|---|
| `kit/launcher/binding.py` | 6–24 | Register deployments, closed milestones and stop ranges. Preserve receipt and claim validation. |
| `kit/launcher/orchard_launcher.py` | 166–167, 204–205 | Require main and/or a7 in prepare and embedded request validation. |
| `kit/launcher/export_stage.py` | 47–48, 92 | Admit the same R1 artifact paths and step ranges at staging. Without this change, a valid preparation would fail staging. |
| `tests/test_fix6.py` | 125–303 | Seven tests cover all reader pins, 37 legacy plans, exhaustive identity refusals, family gates, staging, native export checks and eight manifest comparisons. |
| `tests/test_h1read.py`, `tests/test_kit.py` | 64, 226 | Normalize only the added entry gate when comparing the rest of `stage_export` to the reference. |
| `tools/test_fix3.py`, `tools/seal.py` | Suite dispatch and seal inventory | Add FIX6 tests and evidence; retain fixture write guards and post-seal receipt exclusions. |
| `REPORT.md`, `evidence/INTENDED_PORTS.md` | Current scope and validation | Describe R1 admission and the unchanged reader. |

The archive layout checks, four-part transport, whole-tar size/SHA256 checks and native export checker remain unchanged. `T.EXPORT_RUNS` and legacy `parse_done` remain unchanged: R1 must enter through its validated export binding. Staging accepts a step in the appropriate stop range only after the public path has validated its milestone or claimed generation.

## Packet evidence

Packet roots below are `/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052` (launch) and `/scratch/jjyeung/orch_n30/r1_ops/work/snap_c60b9015` (continuation). Each relative path in this table applies under **both** roots unless stated otherwise. `evidence/FIX6_PACKET_EVIDENCE.json` retains full source hashes and numbered excerpts.

| Fact | Packet file:line | Verified value |
|---|---|---|
| Run and deployment | `out/operator/ids.json:1`; `out/operator/jb.sh:18` | Launch: `673bc60f`, `x_69d2930d`; continuation: `05b8ac69`, `x_7f1589c1`. |
| Namespace and logical export root | `work/tree/launch_s1/b/c.sh:7–10`; `configs/r1p.json:1` (`output`) | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/<run>`. |
| Milestones and stop | `configs/r1p.json:1` (`milestones`, `recipe.milestones`, `h1.stop_after_step`, `recipe.export_at_stop`) | Launch: `[100,200]`, stop 200; continuation: `[400,600]`, stop 600; export-at-stop true. |
| Continuation start | Continuation `configs/r1p.json:1` (`continuation`) | Resume run `673bc60f` at step 200; admitted new stop steps begin at 201. |
| Session names | `out/operator/jb.sh:46–49` | Launch m100/m200; continuation m400/m600; both mstop/mstopB/mstopC, each `.part00-of-04` through `.part03-of-04`. |
| KH/HM binding | `work/tree/launch_s1/b/r.sh:9–10`; `b/c.sh:12,20` | `TK_KIT_HOME` is the deployed kit root; `HX=TK_KIT_HOME`, `HM=HX`. |
| Export scan and object | `work/tree/launch_s1/b/c.sh:408–412` | Scan `<NR>/<run>/m<step>/artifact.json`; object `q8/8865619b/<run>_m<step>.tar`. |
| Stop object and claim | `work/tree/launch_s1/b/c.sh:418–423` | Object `q8/8865619b/<run>_<generation>.tar`; claim `<KH>/o/gcs_<run>_<generation>.claim`, bytes `m<step>\n`; an existing claim can be reused only for the same step. |
| Archive layout and upload | `work/tree/launch_s1/b/c.sh:428–429` | Tar root `m<step>/`; uploader splits into four ordered parts. |
| Completion receipt | `work/tree/launch_s1/b/c.sh:411,430` | `<KH>/o/gcs_<run>_m<step>.done`, bytes `<object> <tar bytes> <tar sha256>\n`; the filename uses the actual optimizer step even for stop objects. |
| Artifact writer | `work/tree/student_pilot/carrier_c1_run.py:2417–2422,2064–2068`; `configs/r1p.json:1` | Export `output/m<step>`, then write `artifact.json` with the optimizer step. The resulting absolute path is `.../8865619b/runs/<run>/m<step>/artifact.json`. |

Every format matches the existing binding and staging conventions. No packet-specific naming deviation was required. These are packet facts; no remote upload, receipt or running job was inspected.

## Identity and manifest proof

`evidence/FIX6_AUDIT.json` records all reader pins, the three changed launcher files, 37 FIX5 fixture configurations and their hashes, and eight manifest fixture paths. The preserved FIX5 launcher sources match the authenticated FIX5 pins. Every legacy plan retains its exact serialized bytes and `plan_sha256`, covering D0/H1-1 m100/m200 with four family selections and both filters, all three H1-1 stop generations, and both step-544 preparations.

Legacy CONFIG files differ only in `launcher_pins`, `launcher_review` and `launcher_review_pin`, which authenticate the launcher change. Their reader payload bytes, payload pins, assets and behavioral fields are identical. Whole-CONFIG byte equality is therefore not claimed.

The CLI fixtures prepare `673bc60f` m100/m200 and `05b8ac69` m400/m600 with `--families main a7 --types direct`. Fresh isolated CPU processes execute the unchanged main binder and a7 request builder. Their evaluator digest, decoding, arm and filter match the FIX5 step-544 preparation. A7's item file matches that preparation; main's item file matches the main contract carried in the same unchanged FIX5 payload and a FIX5 main preparation. Step 544 itself remains a7-only.

The manifest writer needs completed-read receipts, which prepare alone cannot produce. The fixtures therefore supply explicitly synthetic completion receipts and rows from the actual selected item populations. They mock export/frame admission and stop before generation. The registered `build_manifest.py` is copied unchanged to `evidence/FIX6_build_manifest.py` (SHA256 `699cacd7b80608af41f3f5f533b6f12fdd3adaad1e99cde3de065bde9db9b755`) and executed through its CLI entry point for both sets on all four fixture builds.

All eight `config` blocks equal their registered baseline blocks exactly:

| Field | Equal value |
|---|---|
| Arm and evaluator digest | direct; `d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa` |
| Decoding | Greedy, 32 anchors duplicated, thinking on, temperature 0, 16,384 tokens, model length 49,152, engine 0.32.0, budget 2,048 |
| Main item-file SHA256 | `a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e` |
| A7 item-file SHA256 | `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b` |
| Rule population | dev-S1: seven types × 150 = 1,050; R0-dev: 1,781, with every registered per-type count equal |
| Selector, scale and tower weights | The registered direct-arm constants |

The separate top-level `type_filter` is `direct`. It matches R0-dev; dev-S1's baseline is `none`, exactly the allowance registered in v3. No config field differs. These tests establish configuration compatibility, not a live GPU result, a complete production return or a pooled decision. Six miniature R1 milestone/stop exports separately pass the unchanged full native checker.

**Continuation limitation:** `pooled_harm_rule_v3.py:58,309–310` requires run `673bc60f` for a decision. It will reject `05b8ac69` as a decision even though this kit can read it and its manifests match. The registration owner must register continuation provenance before using its reads for decisions. No rule, baseline or registration outside this kit was modified.

## Validation

| Suite | Result | Evidence |
|---|---|---|
| Candidate | 124/124 pass | `evidence/FIX6_TESTS.log` |
| FIX6 | 7/7 pass | `evidence/FIX6_NEW_TESTS.log` |
| FIX5 | 6/6 pass | `evidence/FIX6_FIX5_TESTS.log` |
| FIX4 | 10/10 pass | `evidence/FIX6_FIX4_TESTS.log` |
| Step-544 admission | 7/7 pass | `evidence/FIX6_TARGETED.log` |
| Ported readk | 53/53 pass | `evidence/FIX6_READK_PORTED.log` |
| Original reference | 53/53 pass | `evidence/FIX6_READK_REFERENCE.log` |
| Reviewer refute | 4/4 pass | `evidence/FIX6_REFUTE.log` |
| Unfiltered isolated runtime | 4 items pass | `evidence/FIX6_RUNTIME.log` |
| Direct isolated runtime | 3 items pass | `evidence/FIX6_RUNTIME_DIRECT.log` |

REPORT.md gives the exact suite and sealing commands. Fixture writes stay under `evidence/test_*`. No network, SSH, Slurm, GPU, Git or deletion operation was used. No production preparation or submission was made. The tests retain the original reference source, assets and `kit/build/*`.

## Operator commands: run 673bc60f, boundary 200

These commands were not executed. Use the pinned uploads in UPLOAD_PLAN.md, the completed m200 export receipt and an authorized allocation. This prepares one fresh-token read containing both families, executed sequentially in isolated workers.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
R1_READ=$PWD/kit/build/$TOKEN
"$PY" -B "$L" prepare --run 673bc60f --namespace 8865619b \
  --step 200 --families main a7 --types direct \
  --token "$TOKEN" --destination "$R1_READ"
CMD=$("$PY" -B "$L" submit-command --destination "$R1_READ")
timeout 300 bash "$A_TRANSPORT" "$CMD" < "$R1_READ/BATCH.sh" \
  > "$R1_READ/SUBMIT.out" 2> "$R1_READ/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$R1_READ"
```

After completion, fetch the same destination. In a new shell, restore `R1_READ` to that directory; do not mint another token.

```bash
"$PY" -B "$L" fetch --destination "$R1_READ"
# For a return >=20 MB, fetch retains EXIT.json and prints the exact transfer
# command. Register that stream with the IO governor and execute it once.
"$PY" -B tools/unpack_return.py --destination "$R1_READ"
```

Build both provenance manifests from the complete return. The artifact in `metadata/EXPORT_ARTIFACT.json` is the unchanged training artifact retained by `orchard_job.py:265`. Authenticate it against SPEC, then place those same bytes under the run/step layout required by the pooled-rule CLI. The script refuses an existing output artifact.

```bash
POOLED=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule
"$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" R0-dev "$R1_READ/R0-dev_MANIFEST.json"
"$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" dev-S1 "$R1_READ/dev-S1_MANIFEST.json"
"$PY" -B - "$R1_READ" <<'PY'
import hashlib, json, sys
from pathlib import Path
build = Path(sys.argv[1])
x = build/'fetched/x'
spec = json.loads((x/'SPEC.json').read_text())
raw = (x/'metadata/EXPORT_ARTIFACT.json').read_bytes()
assert spec['export_binding']['run'] == '673bc60f' and spec['step'] == 200
assert hashlib.sha256(raw).hexdigest() == spec['artifact']['sha256']
assert json.loads(raw)['step'] == 200
out = build/'runs/673bc60f/m200/artifact.json'
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('xb') as stream:
    stream.write(raw)
PY
"$PY" -B "$POOLED/pooled_harm_rule_v3.py" --step 200 \
  --read "$R1_READ/fetched/x/ITEMS.jsonl" \
  --manifest-s1 "$R1_READ/dev-S1_MANIFEST.json" \
  --manifest-r0 "$R1_READ/R0-dev_MANIFEST.json" \
  --export-receipt "$R1_READ/runs/673bc60f/m200/artifact.json" \
  --ledger "$POOLED/READ_LEDGER.jsonl" \
  --output "$R1_READ/R1_200_POOLED.json"
```

The last command is the registration's operator workflow and writes its shared ledger. It was not executed under this task's read-only access to that directory. The rule must be registered before the first R1 export is read. Step 100 is calibration only: the registration uses `--calibration --step 200` for those levels, while the manifest and export receipt retain the actual step 100.

## Wall-time estimate

Orchard 171197 (`kit/build/adff67f7ae9/fetched/x/SUMMARY.json:104`) records 768.974 seconds for the 1,781-item a7 chain; its total wall time was about 17 minutes. Main contains 1,525 items and retains 1,339 after removing 150 absolute-distance and 36 room-size items. The retained counts are 150 each for route planning, direction easy/medium/hard, counting, object size, relative size and relative distance, plus 139 relative-count items. The pooled rule uses 1,050 of these; the remaining 289 still execute.

At a7's average throughput, main adds `769 × 1339 / 1781 ≈ 578 seconds`. Reusing the observed approximately 251 seconds of non-chain overhead gives `769 + 578 + 251 ≈ 1,598 seconds`, or **about 27 minutes for main+a7 direct**. Allow roughly 30–35 minutes for planning because prompt lengths, main frame staging and continuation work may differ. This is an extrapolation, not a measured filtered-main runtime; the six-hour allocation remains unchanged.

FIX6.md and post-seal verification logs stay outside the manifest to avoid circular hashes. The operator shell blocks pass `bash -n`; no operator command was executed.

The final pin test passes, and all 223 checksum entries verify. Evidence: `evidence/FIX6_FINAL_PIN_TEST.log`, `evidence/FIX6_SHA256_CHECK.log` and `evidence/FIX6_SEAL.log`.

- FINAL_PINS SHA256: `7891b795c3d0600ac2e45689c13ccf200756cfc450581ca485fff2105abb488b`.
- SHA256SUMS.txt SHA256: `2c57d20a65104f405142eeaaf5ef3cae5c82833cb3f88d6dcd47eae26d49eeb2`.
