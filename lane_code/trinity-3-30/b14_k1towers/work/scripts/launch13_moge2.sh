MODEL=moge2; CARD=4; ORCHCARD=events/b14_k1towers/20261116T1318Z_ORCH_CARD_trinity-1-13_4.md
# run on trinity-1-13 via tssh; header sets MODEL CARD ORCHCARD
set -u
S=/dev/shm/jjyeung/b14; K=$S/geo_bakeoff_kit; date -u
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader -i $CARD
nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader
du -sh /dev/shm/jjyeung $S
python3 - <<PY
import json, hashlib, os
led = [json.loads(l) for l in open('$K/assets/downloads.jsonl')]
fn = 'model.pt' if '$MODEL' == 'moge2' else 'model.safetensors'
r = next(r for r in led if r['path'].endswith('/$MODEL/' + fn) and r['verified_expected_sha256'])
h = hashlib.sha256(); f = open('$K/assets/$MODEL/' + fn, 'rb')
for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
print('WEIGHT_SHA', 'OK' if h.hexdigest() == r['sha256'] else 'MISMATCH')
PY
cd $S/code && sha256sum *.py
mkdir -p $S/out/$MODEL $S/tmp $S/logs
printf 'GO trinity-1-13 card %s for %s per %s\n' $CARD $MODEL "$ORCHCARD" > $S/GO_card$CARD.txt
cat > $S/logs/run_$MODEL.sh <<EOS
source $K/work/kit_env.sh; set +e
export TMPDIR=$S/tmp XDG_CACHE_HOME=$S/tmp/cache HF_HOME=$S/tmp/hf TORCH_HOME=$S/tmp/torch CUDA_VISIBLE_DEVICES=$CARD
cd $S/tmp
/data3/shared/scripts/vnice/vnice.sh $K/runtime/base/bin/python3 $S/code/k1_infer.py --model $MODEL --manifest $S/K1_MANIFEST.arkit_timing.json --towers $S/k1/run_tower_sam_2 --out $S/out/$MODEL --device cuda --go-file $S/GO_card$CARD.txt --threads 8 --frame-prefix /scratch/jjyeung/k1_frames=$S/k1_frames > $S/logs/run_$MODEL.log 2>&1
echo EXIT \$? >> $S/logs/run_$MODEL.log
EOS
cat $S/logs/run_$MODEL.sh | tail -2
tmux new-session -d -s b14_$MODEL "bash $S/logs/run_$MODEL.sh"
sleep 90; tail -c 1500 $S/logs/run_$MODEL.log; cat $S/out/$MODEL/progress.jsonl 2>/dev/null | tail -3
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader -i $CARD
