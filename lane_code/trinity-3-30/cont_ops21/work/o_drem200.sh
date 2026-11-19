# cont_ops21: D@200 remainder build (REPORT_DREM400.md sequence with the 200 binding); stops after the CPU-check submission
set -euo pipefail
export KROOT=/project/community/jjyeung/okh7; export KIT=$KROOT/813f42db/c20d400rcode/dresume
export PARENT="$KROOT/a15_cot_apd296bd1ef61cd" STAGE="$KROOT/813f42db/c21d200r" WORK="$KROOT/813f42db/c21d200r-input" T=04:00:00
cd $KIT; mkdir -m 700 "$WORK"
/usr/bin/python3 -B -c 'import sys,tarfile; from pathlib import Path; t=tarfile.open(sys.argv[1]+"/0.tgz"); Path(sys.argv[2]).write_bytes(t.extractfile("items/dist580.json").read())' "$PARENT" "$WORK/full.json"
R=$(/usr/bin/python3 -B -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$PARENT")
PART="$KROOT/ae71c903/$R"; test -d "$PART" || PART="$KROOT/ae71c903_fetched/$R"; export PART; echo PART $PART
/usr/bin/python3 -B "$KIT/make_items_remainder.py" --items "$WORK/full.json" --package "$PARENT" --archive "$PART/result.tar.gz" --exit "$PART/EXIT.json" --receipt "$PART/RETURN_RECEIPT.json" --work "$WORK/unpacked" --out "$WORK/REMAINDER.json"
/usr/bin/python3 -B -c 'import json,sys; d=json.load(open(sys.argv[1])); print("remainder items", len(d["items"]) if "items" in d else list(d)[:8])' "$WORK/REMAINDER.json"
/usr/bin/python3 -B "$KIT/build_remainder.py" --stage "$STAGE" --source "$KROOT/a15_cot_ap4e8c539166092f0c/1.tgz" --source-sha c3187ab9f88b3eb5a7ab1e30a8010e4ef86acb49d6c76e98fd97eec393b4e45a --items "$WORK/REMAINDER.json" --binding "$KIT/dbuild/bind_D200.json" --time "$T"
export REUSE_PARTS_FROM="$PARENT/a/e" PREP_FROM="$PARENT/a/e"
/usr/bin/python3 -B "$STAGE/place_fill_d.py" "$STAGE"
export P=$(/usr/bin/python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["D"]["package"])' "$STAGE/BUILD.json"); echo P $P
stat -c 'links=%h %n' $P/a/e/0
bash "$STAGE/o_cpu_D.sh"; echo CPU_SUBMITTED; cat $P/a/4.txt 2>/dev/null
