set -u
B=/dev/shm/jjyeung/b04/host; L=$B/b04_e2ehook; T=$B/tree_rebuild/work/base/tree_b01ce449
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=/dev/shm/jjyeung/b04/pyoverlay; O=$L/parity_kit/host_restore; R=$L/parity_kit/host_results
wc -l $R/cpu_first_b/items.jsonl; head -c 600 $R/cpu_first_b/items.jsonl; echo; cat $R/cpu_first_b/LOAD_TIMING.json | head -c 400; echo
$PY -c "
import json; s=json.load(open('$L/parity_kit/settings.json')); s['env_roots']=['$OV']; json.dump(s, open('$L/parity_kit/settings.json','w'))"
cd $L && PYTHONPATH=$OV timeout 120 $PY -B -m parity_kit.sam3_probe --source-root /dev/shm/jjyeung/b05/stage/sam3src --checkpoint /dev/shm/jjyeung/b05/stage/sam3.pt --tree $T 2>&1 | grep -v Warn | tail -25
ls -la /scratch/jjyeung | grep -i "b05\|sam3" | head
cat > $L/work/host_run_c.sh <<SH
set -u
cd $L
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp OMP_NUM_THREADS=32 CUDA_VISIBLE_DEVICES=
mv $L/parity_kit/E2E_MANIFEST.json $L/parity_kit/E2E_MANIFEST.v2.json; mv $L/parity_kit/E2E_MANIFEST.binding.json $L/parity_kit/E2E_MANIFEST.binding.v2.json
nice -n 10 $PY -B -m parity_kit.build_manifest --root /dev/shm/jjyeung --export-dir $O --g3t /dev/shm/jjyeung/b04/k1/g3t --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST.json > $L/work/manifest_c.log 2>&1
nice -n 10 $PY -B -m parity_kit.cpu_first_batch --settings $L/parity_kit/settings.json --arm own_depth --device cpu --out $R/cpu_first_c > $L/work/first_c.log 2>&1; echo FIRST_DONE >> $L/work/first_c.log
SH
tmux new-session -d -s b04_first "bash $L/work/host_run_c.sh"; sleep 1; tmux ls | grep b04
