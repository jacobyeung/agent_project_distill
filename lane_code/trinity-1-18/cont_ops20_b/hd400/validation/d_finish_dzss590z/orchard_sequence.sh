export STAGE=/project/community/jjyeung/okh7/813f42db/cont_ops20_d400 STEP=400 WALLTIME=04:00:00 SOURCE_1TGZ=/project/community/jjyeung/okh7/a15_cot_ap4e8c539166092f0c/1.tgz
bash o_build_D.sh
export REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done
bash o_place_fill_D.sh
export P=$(/usr/bin/python3 -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["D"]["package"])' "$STAGE/BUILD.json") T=04:00:00
bash o_cpu_D.sh # Wait for a successful CPU receipt before o_sub_D.sh.
bash o_sub_D.sh # Wait for the GPU job to end before fetching.
R=$(/usr/bin/python3 -B -c 'import json,sys;from pathlib import Path;p=Path(sys.argv[1]);print(json.loads((p/"0.json").read_text())["token"]+"%08x"%int((p/"a/8.txt").read_text()))' "$P"); /usr/bin/python3 -B "$P/3.py" fetch --return-token "$R" --out "$STAGE/return"
