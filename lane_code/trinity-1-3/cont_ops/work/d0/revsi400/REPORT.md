The kit prepares ReVSI official999 tier-32 direct reads at steps 200/400/600/800/1000 from run 359fcc3c, lineage 8865619b. Step 400 is the default. This read supplies a ranking number and makes no stopping decision. B2048 is primary; ON16k and B4096 accompany it.
The authenticated source package is ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b. All evaluator, item, cohort/frame-plan, scorer, and export-checker bytes match it. DIFF.md labels every changed line; REVIEW.md maps changes to code.
Step 544 is complete: each arm has 679 unique, complete item records on the same 261 scenes. The recovered packet is evidence/reference544; its source archive SHA256 is 785a097ff750fc3d82a5ffd18cb299527fbe1e207d5166c86326edddd21c2036. See evidence/REFERENCE_COMPLETENESS.json.
paired.py calls the unchanged kit/reader/official_score.py:130 paired() function. It uses 10,000 joint scene draws, seed 544, equal subtype means within categories, and an equal five-category mean. Subtype intervals use the identical sorted-scene multinomial draws. It reports current minus 544, the four facing leaves, and toward/away text diagnostics for all three arms. Values are fractions. Membership, task/prompt/media/processor metadata, checkpoint identity, and protocol mismatches fail closed.
The two limits are **21 minutes for proof and 25 minutes for production**, with clean-stop initiation three minutes before the limit and return cleanup bounded 30 seconds inside it. Proof 170035 measured 9m02s between card observations; production 170037 measured 12m44s in the supplied job record. Adding readk's 497.6s staging measurement and 180s cleanup gives 20m20s and 24m02s, rounded upward. These allowances conservatively add staging to durations that already include staging.
Budget 160 GB of additional job-private /tmp space; start with at least 380 GB free, including the unchanged 200 GiB floor. This is an estimate from the accepted 21.583 GB export, runtime/base archives, extracted weights, one staged model pair, frames, and return space. Each job stages separately.
The job name is a15_cot_ap followed by hex. New pool/GCS roots and interpreter aliases are opaque; preparation writes token meanings only to LEDGER.jsonl here. Legacy unused code trees are not extracted, and diagnostics are hex-encoded, including native child output. Installed third-party runtime filenames have not been audited against the literal “any Orchard path” restriction; unconditional naming compliance is not claimed.
Run this block locally from this folder. Submit only after the corresponding receipt lands (m400 is expected about 2026-11-17 01:40Z). All remote commands use the required wrapper; the builder ran none.
```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/d0/revsi400
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
STEP=400
P=$PWD/kit/build/$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')
Q=$PWD/kit/build/$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')
timeout 300 bash "$OSSH" "test -s /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m${STEP}.done"
"$PY" -B "$L" prepare --mode proof --step "$STEP" --token "${P##*/}" --destination "$P"
CMD=$("$PY" -B "$L" submit-command --destination "$P")
timeout 300 bash "$OSSH" "$CMD" < "$P/BATCH.sh" > "$P/SUBMIT.out" 2> "$P/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$P"
"$PY" -B "$L" prepare --mode production --step "$STEP" --proof-destination "$P" --token "${Q##*/}" --destination "$Q"
CMD=$("$PY" -B "$L" submit-command --destination "$Q")
timeout 300 bash "$OSSH" "$CMD" < "$Q/BATCH.sh" > "$Q/SUBMIT.out" 2> "$Q/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$Q"
```
Production requires afterok on the recorded proof job and identical payload/code/step/media. Both submissions run test-only admission before the real stdin submission. The proof keeps the same ten-item selection, processor parity, and all-video frame checks used by 170035; the optional extra engine phase remains disabled. Do not rerun an uncertain or killed submission.
After completion, fetch both returns. The fetch implementation invokes `timeout 300 bash "$OSSH" <exact remote command>` internally for every channel. At 20 MB it prints the exact governed transfer command and stops for registration.
```bash
"$PY" -B "$L" fetch --destination "$P"
"$PY" -B "$L" fetch --destination "$Q"
"$PY" -B unpack_result.py --destination "$Q" --output "$Q/packet"
"$PY" -B paired.py --step "$STEP" --current "$Q/packet" --reference evidence/reference544 --output "$Q/PAIRED.json"
```
Validate locally with the guarded suite and a fresh synthetic proof directory:
```bash
"$PY" -B run_tests.py kit/tests tests -q
"$PY" -B kit/proof/run.py --work "$PWD/evidence/proof_$("$PY" -B -c 'import secrets;print(secrets.token_hex(6))')"
"$PY" -B tests/parity_local.py
"$PY" -B audit_build.py
```
Evidence: FINAL_TESTS.log records the guarded suite (106 tests); FINAL_LOCAL_PROOF.log records five full-cohort binds with identical accepted prompt-pin bytes and the synthetic worker/budget/scorer proof; FINAL_PARITY.log verifies the accepted dev prompt pins using the packaged reader; AUDIT.log and FINAL_PINS.json pin the build; PAIRED_EXECUTED_LINES.json covers every executable function statement in paired.py. Synthetic fixtures do not measure model quality.
Unverified: live receipt/weights, credentials, installed runtime closure and private filenames, real processor execution, all 261 real video pixels, H100/vLLM execution, actual milestone timing/storage, and live return publication. The scorer reports no m400 result before those data exist. No SSH, network, GPU, Git, deletion, or Slurm action ran.
