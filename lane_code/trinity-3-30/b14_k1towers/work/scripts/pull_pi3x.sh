set -u
S=/dev/shm/jjyeung/b14; date -u
tail -n2 $S/logs/run_pi3x.log
grep -q "^EXIT 0" $S/logs/run_pi3x.log || { echo MOGE2_NOT_DONE; tail -n2 $S/out/pi3x/progress.jsonl; exit 1; }
python3 -c "
import json,collections;r=[json.loads(l) for l in open('$S/out/pi3x/progress.jsonl')];print(collections.Counter(x['state'] for x in r))"
tar cf - -C $S/out pi3x | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "mkdir -p /scratch/jjyeung/orch_n30/geo_k1/pred_gpu && tar xf - -C /scratch/jjyeung/orch_n30/geo_k1/pred_gpu && ls /scratch/jjyeung/orch_n30/geo_k1/pred_gpu/pi3x | wc -l && echo PULLED_OK"
du -sh $S $S/out; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader -i 4
