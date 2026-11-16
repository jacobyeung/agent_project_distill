set -u
S=/dev/shm/jjyeung/b11_presence
date -u +%FT%TZ; hostname -s
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
nvidia-smi -i 1 --query-compute-apps=pid,used_memory --format=csv,noheader
used=$(nvidia-smi -i 1 --query-gpu=memory.used --format=csv,noheader,nounits)
[ "$used" -lt 100 ] || { echo "CARD1 BUSY $used"; exit 5; }
mkdir -p /scratch/jjyeung/k1_frames /scratch/jjyeung/orch_n30/b11_presence /scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader
mkdir -p $S/lane/work/model_m544 $S/lane/work/logs $S/cache
cat > $S/bw.sh <<'EOS'
#!/bin/bash
S=/dev/shm/jjyeung/b11_presence
exec bwrap --dev-bind / / --bind $S/lane /scratch/jjyeung/orch_n30/b11_presence \
  --bind /dev/shm/jjyeung/exports/m544 /scratch/jjyeung/orch_n30/b11_presence/work/model_m544 \
  --bind $S/k1_frames /scratch/jjyeung/k1_frames \
  --bind $S/reader /scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader \
  --setenv CACHE_ROOT $S/cache "$@"
EOS
chmod +x $S/bw.sh
$S/bw.sh bash -c 'cd /scratch/jjyeung/orch_n30/b11_presence && ls code && ls work/model_m544 | wc -l && head -c 200 out/prep/PREP_SUMMARY.json && python3 -c "import json;c=json.loads(open(\"out/prep/CAPTURES.jsonl\").readline());import os;print(all(os.path.isfile(f) for f in c[\"frames\"]))" && ls /scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader/evaluator/parity.py' || { echo BWRAP_SANITY_FAIL; exit 6; }
tmux new-session -d -s b11gpu "$S/bw.sh bash /scratch/jjyeung/orch_n30/b11_presence/code/run_gpu.sh 1 > $S/lane/work/logs/run_gpu.outer.log 2>&1"
sleep 20; tmux ls | grep b11; cat $S/lane/work/logs/run_gpu.log 2>&1 | tail -3
