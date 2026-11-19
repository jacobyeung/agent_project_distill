T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; date -u +%TZ
sed -n 1,20p $T/launch_r1/entry.py </dev/null | cut -c1-250
sed -n 150,215p $T/launch_r1/entry.py </dev/null | cut -c1-220
grep -n "^def \|frame_host\|host_receipt\|def run\|def _run" $T/launch_r1/production_proof.py </dev/null | head -30 | cut -c1-200
