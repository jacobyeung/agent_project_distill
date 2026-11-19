H400 is built and locally validated; D400 code is ready, but its full build validation is blocked.
Both bindings use in/BIND400.json, authenticated A10b part pins, and matching export/preparation hashes.
Builders and generated scripts admit STEP=400 for 6ed2c7aa/m400; D now checks complete sealed-binding equality.
Both fill drivers require reuse and the exact x_ee227714/o/gcs_6ed2c7aa_m400.done path for step 400.
Preparation hashes and receipt contents fail closed; all parts pass before linking. D400 cannot download or copy on link failure.
Both scorers admit EXPORTS[400] with package/plan/operator, export, preparation and journal identity checks.
Payload, operator, items, settings and 04:00:00 walltime retain the step-544 definitions.
H retains 900 items and a fitting budget; D retains 580 items and its non-fitting four-hour budget.

Validation outputs are under validation/. No SSH, network, Git, deletion, GPU or submission ran.
H test_h.py passed for 200/400/544: 900 mappings, 3,816 parity cases and 900 response stubs per build.
H review_h.py, test_place_h.py, test_scripts_h.py and score_h.py --self-test passed.
The regenerated o_build_H.sh also built STEP=400 under a local KROOT.
New H tests accept 400, reject 544-as-400 and wrong exports, and pass the 400-versus-544 CLI comparison.
DIFF_H400_VS_H544.txt verifies that only tokens, export binding and derived pins differ.
D test_score_identity_d.py passed all nine tests, including synthetic 400 identity/refusals and comparison.
D's complete scoring self_test passed using the authenticated original scorer from A4.
Both actual builder admission blocks reject eight binding mutations; both actual fill blocks reject nine corruptions before linking.
Both regenerated scripts' embedded assets match their source files. Python 3.6.8 compiled 44 files; bash -n passed 101 scripts; 20 embedded Python blocks parsed.
D test_d.py, test_followup_d.py and check_release_d.py were attempted but lack source/build fixtures.
D's B5 source and its old temporary deliveries are absent; supplied evidence excludes full archives.
DIFF_D400_VS_D544.txt records the missing bytes; it is not a successful comparison.
Required: local B5 1.tgz, SHA256 c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a, or complete B5 package.
D's full builds, release/CPU-guard checks and byte comparison remain pending that input.

Orchard H sequence, from the directory containing H helpers:
```bash
export STAGE=/project/community/jjyeung/okh7/813f42db/cont_ops20_h400 STEP=400 WALLTIME=04:00:00
bash o_build_H.sh
export REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e
export DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done
bash o_place_fill_H.sh
export P=$(/usr/bin/python3 -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["H"]["package"])' "$STAGE/BUILD.json") T=04:00:00
bash o_cpu_H.sh
# Wait for a successful CPU receipt before the next command.
bash o_sub_H.sh
# After the GPU job ends, derive its authenticated return token and fetch.
R=$(/usr/bin/python3 -B -c 'import json,sys;from pathlib import Path;p=Path(sys.argv[1]);print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$P")
/usr/bin/python3 -B "$P/3.py" fetch --return-token "$R" --out "$STAGE/return"
```
Orchard D sequence, after pending local validation, from the directory containing D helpers:
```bash
export STAGE=/project/community/jjyeung/okh7/813f42db/cont_ops20_d400 STEP=400 WALLTIME=04:00:00
bash o_build_D.sh
export REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e
export DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done
bash o_place_fill_D.sh
export P=$(/usr/bin/python3 -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["D"]["package"])' "$STAGE/BUILD.json") T=04:00:00
bash o_cpu_D.sh
# Wait for a successful CPU receipt before the next command.
bash o_sub_D.sh
# After the GPU job ends:
R=$(/usr/bin/python3 -B -c 'import json,sys;from pathlib import Path;p=Path(sys.argv[1]);print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$P")
/usr/bin/python3 -B "$P/3.py" fetch --return-token "$R" --out "$STAGE/return"
```

## D finish

`test_d.py`, `test_followup_d.py` and `check_release_d.py` passed; D400 also passed release, identity/comparison and 21 synthetic CPU-guard refusals. Results: `validation/d_finish_dzss590z/RESULTS.json`.
`DIFF_D400_VS_D544.txt` verifies that only token-derived bytes, export binding and derived pins differ; payload code, operator, 580 items, settings and 04:00:00 remain unchanged. Both budgets remain non-fitting. No defects required fixes; H files are untouched.

```bash
export STAGE=/project/community/jjyeung/okh7/813f42db/cont_ops20_d400 STEP=400 WALLTIME=04:00:00 SOURCE_1TGZ=/project/community/jjyeung/okh7/a15_cot_ap4e8c539166092f0c/1.tgz
bash o_build_D.sh
export REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done
bash o_place_fill_D.sh
export P=$(/usr/bin/python3 -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["D"]["package"])' "$STAGE/BUILD.json") T=04:00:00
bash o_cpu_D.sh # Wait for a successful CPU receipt before o_sub_D.sh.
bash o_sub_D.sh # Wait for the GPU job to end before fetching.
R=$(/usr/bin/python3 -B -c 'import json,sys;from pathlib import Path;p=Path(sys.argv[1]);print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$P"); /usr/bin/python3 -B "$P/3.py" fetch --return-token "$R" --out "$STAGE/return"
```
