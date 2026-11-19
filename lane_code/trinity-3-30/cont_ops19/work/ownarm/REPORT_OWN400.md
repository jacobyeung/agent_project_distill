The own-arm camera kit is built at `out/pkg/r400` for run `6ed2c7aa`, step 400. Local checks pass; nothing was submitted.

The builder accepts only the run/receipt-directory pairs `673bc60f/x_69d2930d` and `6ed2c7aa/x_ee227714`, with exact run and step in the receipt name. A changed run requires the complete binding and preparation paths. Both pull scripts copy the three pinned preparation files and verify their SHA-256 hashes before downloading export parts. Unknown runs, inconsistent paths, incomplete preparation pins and malformed hashes fail closed.

`pin400.json` equals `BIND400.json` plus `part_bytes: 5395758080`. Binding values, archive pins and fill step come from this pin. Step 600 is covered by a synthetic acceptance test; it needs its own real export pin.

The delivery exactly reproduces a reseal of b200 with only token, export binding and `REVIEWED_*` changes. All 926 payload members other than `9.json`, the operator, tower settings and item order remain identical. `DIFF_R400_VS_B200.txt` includes every script's unified diff; identical scripts have explicitly empty diffs. Build metadata and dependent hashes reflect the rebind.

Token: `fadf2291c654b`. The matching line remains in `out/pkg/TOKEN_LEDGER.jsonl`.
Delivery: `out/pkg/r400/1.tgz`.
Delivery SHA-256: `359151d1aafc9128b42f6e3b3a788cecc5aaf510fe57219f8367290a1afdd61a`.

The snapshot lacks the original A4 directory. `snapshot_inputs.py` reconstructs its archive and requires the exact reviewed SHA-256 `dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459`. Its A templates reproduce all six b200 scripts exactly. Scorer tests use synthetic metadata with pinned reference rows; vendor files match their recorded hashes.

These commands passed from the workspace; use fresh work/output paths when reproducing them:
```bash
export PY=/scratch/jjyeung/envs/p1cpu/bin/python
export TMPDIR=/dev/shm/c19o/w/tmp PYTHONDONTWRITEBYTECODE=1
export A4=/dev/shm/c19o/w/inputs3/A4 A=/dev/shm/c19o/w/inputs3/A
export PROOF=/dev/shm/c19o/w/inputs3/proof
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=
$PY -B kit/tests/snapshot_inputs.py /dev/shm/c19o/w/inputs3
$PY -B kit/build_ownread.py --a4 "$A4" --a "$A" --export-pin pin400.json --out out/pkg/r400 --work-dir /dev/shm/c19o/w/r400
$PY -B -m pytest -q -p no:cacheprovider --basetemp=/dev/shm/c19o/w/pytest400 kit/tests/test_kit.py
$PY -B kit/tests/check_build.py out/pkg/r400
$PY -B kit/tests/audit_rebind.py out/pkg/r400 /dev/shm/c19o/w/syntax400_complete DIFF_R400_VS_B200.txt
```
Results: 71 tests passed in 73.73 seconds, with no skips. `check_build.py` passed. The audit passed `bash -n` on all 32 scripts and both embedded fill scripts, and `py_compile` on 39 Orchard helpers/embedded Python blocks using actual Python 3.6.8. Preparation-guard tests reject a valid-length wrong hash for each file in both pull scripts. Logs are preserved in `TEST_RESULTS_OWN400.txt`; the helper inventory is in `out/pkg/r400/VALIDATION.json`.

The local `--work-dir` option keeps extracted package/source trees under `/dev/shm/c19o/w`; `out/pkg/r400` links to them. The archive and operational scripts are regular workspace files. Builder temporary imports honor `TMPDIR`.

For Orchard, stage `out/pkg/r400/1.tgz` and its six `o_*.sh` scripts in the fresh directory D below. Run the following sequence on Orchard only after staging and launch authorization:
```bash
export D=/project/community/jjyeung/okh7/a15_cot_ap7e4d49a0f823
P=/project/community/jjyeung/okh7/a15_cot_apfadf2291c654b
cd "$D"
D="$D" bash o_place.sh
bash o_pullfill.sh
# Wait for the background fill to finish successfully; do not continue on failure.
test "$(cat "$P/a/1.txt")" = 0
bash o_cpucheck.sh
# Wait for the CPU job in a/4.txt to finish; o_sub checks its complete CPU receipt.
bash o_sub.sh
# Wait for the GPU job in a/8.txt to reach a terminal state.
bash o_fetch.sh
```
`o_pullfill_resume.sh` is only for the existing part-0-only state after the original fill has stopped; it rechecks the receipt and preparation files. Downloads retain zero retries. The regular sequence uses one GPU and a five-hour limit.

Open risks: this package has not run an Orchard CPU check or GPU job. Local checks cannot verify the current remote receipt, preparation files or export parts; Orchard checks enforce those pins. The scorer fixture is not a measurement. Extracted trees in `/dev/shm` are temporary; the self-contained delivery archive persists in the workspace. Use `pin400.json` and this report for this run; the unchanged generic operator note contains step-200 examples.
