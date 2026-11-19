c20_revdrem: 1 windows (created Thu Nov 19 12:25:07 2026)
D remainder tooling accepts steps 200, 400 and 544 with the reviewed dbuild binding checks.
The 400 binding, fill driver and base scorer match dbuild byte for byte; return helpers inherit the scorer's export checks.
Tests: test_remainder.py passed for 200/400/544 using in/B5_1.tgz; each kept all 10 rejection checks.
Each synthetic 330+250 merge passed the selection/build/scoring CLIs and produced 580 rows and 290 pairs.
The 250-item remainder seals 04:00:00, with a fitting 9,470 GPU-second budget; actual count depends on the partial.
Step-400 guard tests passed 33 refusals and four authenticated hardlinks, including refusal to copy after link failure.
Evidence: validation/drem{200,400,544}/TEST_RESULTS.json and validation/drem400_guards/TEST_RESULTS.json.
All return fixtures are synthetic, including the B5 restore fixture. No real fill, CPU allocation or GPU run was tested.
No SSH, network, Git, deletion or submission ran. All generated files stay in this workspace.

Run from the deployed dresume directory on Orchard after the parent's verified partial publication:
```bash
set -euo pipefail
export KIT="$PWD" KROOT=/project/community/jjyeung/okh7
export PARENT="$KROOT/a15_cot_apda6f7936c1779" STAGE="$KROOT/813f42db/c20d400r" WORK="$KROOT/813f42db/c20d400r-input" T=04:00:00
mkdir -m 700 "$WORK"
/usr/bin/python3 -B -c 'import sys,tarfile; from pathlib import Path; t=tarfile.open(sys.argv[1]+"/0.tgz"); Path(sys.argv[2]).write_bytes(t.extractfile("items/dist580.json").read())' "$PARENT" "$WORK/full.json"
R=$(/usr/bin/python3 -B -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$PARENT")
export PART="$KROOT/ae71c903/$R"
/usr/bin/python3 -B "$KIT/make_items_remainder.py" --items "$WORK/full.json" --package "$PARENT" --archive "$PART/result.tar.gz" --exit "$PART/EXIT.json" --receipt "$PART/RETURN_RECEIPT.json" --work "$WORK/unpacked" --out "$WORK/REMAINDER.json"
/usr/bin/python3 -B "$KIT/build_remainder.py" --stage "$STAGE" --source "$KROOT/a15_cot_ap4e8c539166092f0c/1.tgz" --source-sha c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a --items "$WORK/REMAINDER.json" --binding "$KIT/dbuild/bind_D400.json" --time "$T"
export REUSE_PARTS_FROM="$PARENT/a/e" PREP_FROM="$PARENT/a/e" DONE_FROM="$KROOT/x_ee227714/o/gcs_6ed2c7aa_m400.done"
/usr/bin/python3 -B "$STAGE/place_fill_d.py" "$STAGE"
export P=$(/usr/bin/python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["D"]["package"])' "$STAGE/BUILD.json")
bash "$STAGE/o_cpu_D.sh"
# Run the next command only after the new CPU allocation succeeds.
bash "$STAGE/o_sub_D.sh"
# After the remainder publishes its verified return, merge both segments:
R=$(/usr/bin/python3 -B -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$P")
export REST="$KROOT/ae71c903/$R"
/usr/bin/python3 -B - <<'PY'
import json, os
from pathlib import Path
e=os.environ; w=Path(e['WORK']); g=dict(items=str(w/'full.json'),parent_package=e['PARENT'],remainder_items=str(w/'REMAINDER.json'),remainder_package=e['P'])
for prefix,root in [('partial',e['PART']),('remainder',e['REST'])]:
    for key,name in [('archive','result.tar.gz'),('exit','EXIT.json'),('receipt','RETURN_RECEIPT.json')]: g[prefix+'_'+key]=str(Path(root)/name)
with (w/'SCORE_SPEC.json').open('x') as f: json.dump(dict(current=g),f,indent=2)
PY
/usr/bin/python3 -B "$KIT/score_d.py" --spec "$WORK/SCORE_SPEC.json" --work "$WORK/score" --out "$WORK/SCORES.json"
```
