The own-arm camera kit at `out/pkg/r400` targets run `6ed2c7aa`, step 400. Both review findings are fixed. No Orchard job was submitted.

Token: `fadf2291c654b`; its existing `out/pkg/TOKEN_LEDGER.jsonl` entry remains valid.
Delivery: `out/pkg/r400/1.tgz`; SHA-256: `359151d1aafc9128b42f6e3b3a788cecc5aaf510fe57219f8367290a1afdd61a`.
The delivery archive is unchanged. No sealed member required a fix or reseal; the operator, tower settings and payload code remain identical to b200. `pin400.json` is `BIND400.json` plus `part_bytes: 5395758080`.

## Fix round

Both pull scripts embed `kit/dryres2.py` verbatim and the adapted `kit/dry_own.py`; the builder emits the same checks. No additional files need staging. The order is fill, input-resolution check, `3.py check`, package check, then `a/e/10.json` and `a/1.txt`. Shell `set -euo pipefail` prevents either success receipt after a failed check. Reports are `a/e/dryres.json` and `a/e/drypackage.json`.

The input-resolution check retains all `dryres2.py` semantics: part sizes, tar-header/member resolution, pinned file sizes/types, policy authorization, unchanged base slots and the preparation archive pin.
The package check keeps these `dry2.py` checks unchanged:

- `5.payload_sha`, `5.package_descriptor`, `5.sequence_is_a6`, `5.plan_sha`, `stage.payload_pins`, `5.export_pins_load_validate`.
- `prepare.no_optional`, `prepare.types_all_five`, `prepare.prep_members`, `prepare.prep_pins`, `prepare.prep_vs_binding`, `admit.export_binding`, `admit.archive0`.
- `stage.a3_slot_present`, `stage.vnice_sha`, `stage.terminator_sha`, `stage.policy_receipt`; it also retains the environment-version diagnostic.
- `guard.inventory`, `guard.descriptor`, `guard.operator`, `guard.tmp_token`, `5.settings_rule`, `6.rule_in_RULES`, `6.memory_fits`, `sub.job_name`.

`6.descriptor` validates the full own-arm descriptor: types `[0,1,2]`, arms `[tower,own]`, mode `none`, 900 reads and the pinned tower/memo settings. `6.items_636` becomes 450 unique camera items (150/type) × two arms = 900 reads. `6.types_order` checks camera displacement, rotation and movement direction in that order. These replace A4's evaluation selection because this operator reads only camera items. The five-type staging inventory check remains applicable and unchanged.
The added schedule/worker checks execute the real operator `prepare` and runner `worker_args`, requiring one worker per type, separate journals and both arms. They extract the pure `MODES`/`settings` definitions from the sealed memo module with AST; they import no NumPy, Torch or model code. All Orchard checks use Python 3.6 stdlib only.

`out/pkg/r400/package` and `src` are real workspace directories reconstructed from `1.tgz` and its nested `0.tgz`. All 15 package files and 927 payload files match the archives. Local return unpacking and scoring pass with synthetic metadata; this is not an Orchard measurement.

Validation: 71 kit tests and 15 dry-check tests pass. Both pull scripts accept correct fixtures and reject wrong member sizes, export-pin hashes, preparation archive pins and base-slot pins before success. Operator tests reject wrong arms, counts, order and combined workers. `check_build.py` passes. `audit_rebind.py` verifies the exact permitted reseal, all script diffs, `bash -n` on 32 scripts plus two embedded shells, and `py_compile` on 43 helpers/blocks with Python 3.6.8.
Logs: `out/fix400/{kit_tests,dry_tests_verified,check_build,audit,local_return}.log`. `DIFF_R400_VS_B200.txt` includes every script; `out/pkg/r400/VALIDATION.json` records the syntax inventory. `out/pkg/r400/FIX_VALIDATION.json` records the fixed script/helper hashes.

Reproduce from the workspace with fresh output directories:
```bash
export PY=/scratch/jjyeung/envs/p1cpu/bin/python
export TMPDIR="$PWD/out/fix400/tmp" PYTHONDONTWRITEBYTECODE=1
export A4="$PWD/out/fix400/inputs/A4" A="$PWD/out/fix400/inputs/A" PROOF="$PWD/out/fix400/inputs/proof"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=
# The recorded run created inputs with: $PY -B kit/tests/snapshot_inputs.py out/fix400/inputs
$PY -B -m pytest -q -p no:cacheprovider --basetemp="$PWD/out/fix400/recheck_kit" kit/tests/test_kit.py
$PY -B -m pytest -q -p no:cacheprovider --basetemp="$PWD/out/fix400/recheck_dry" kit/tests/test_dry_checks.py
$PY -B kit/tests/check_build.py out/pkg/r400 --a4 "$A4"
$PY -B kit/tests/audit_rebind.py out/pkg/r400 out/fix400/recheck_syntax DIFF_R400_VS_B200.txt
$PY -B kit/tests/check_local_return.py out/pkg/r400 "$PROOF" out/pkg/r400_return_recheck
```

Exact Orchard sequence: stage `1.tgz` and all six `o_*.sh` files from `out/pkg/r400` into the fresh D directory, then run on Orchard:
```bash
set -euo pipefail
export D=/project/community/jjyeung/okh7/a15_cot_ap7e4d49a0f823
P=/project/community/jjyeung/okh7/a15_cot_apfadf2291c654b
cd "$D"
D="$D" bash o_place.sh
bash o_pullfill.sh
# Wait for the background fill to exit successfully; inspect a/0.log on failure.
test "$(cat "$P/a/1.txt")" = 0
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
for name in ('dryres.json', 'drypackage.json', '10.json'):
    assert json.loads((p/'a/e'/name).read_text())['passed'] is True
PY
bash o_cpucheck.sh
# Wait for the CPU job in a/4.txt to finish; o_sub requires its complete receipt.
bash o_sub.sh
# Wait for the GPU job in a/8.txt to reach a terminal state.
bash o_fetch.sh
```
`o_pullfill_resume.sh` applies only to an existing part-0-only fill after its process has stopped. It repeats both dry checks and the receipt/preparation guards. Downloads retain zero retries; the regular run uses one GPU for at most five hours.
Open risks: no Orchard CPU/GPU run or remote-path verification occurred. Synthetic fixtures exercise validation and local return plumbing, not model quality. The unchanged generic operator note contains step-200 examples; use this report and `pin400.json` for r400.
