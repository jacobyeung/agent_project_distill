S=/dev/shm/jjyeung/b05; date -u +%T; tmux ls 2>/dev/null | grep -c b05_pilot2; nvidia-smi -i 2 --query-gpu=memory.used,utilization.gpu --format=csv,noheader
grep -i "error\|traceback\|rc=" $S/pilot2_console.log | tail -3
python3 - <<'PY'
import json
rows=[json.loads(l) for l in open('/dev/shm/jjyeung/b05/pilot2/train.jsonl')]
tr=[r for r in rows if r['event']=='train']
w=tr[-20:]; print('step',tr[-1]['step'],'el',round(tr[-1]['elapsed_seconds']),'total20',round(sum(r['losses']['total'] for r in w)/len(w),3),'dice20',round(sum(r['losses']['mask_dice'] for r in w)/len(w),3))
for v in rows:
    if v['event']=='validation':
        m=v['metrics']; print('VAL',v['step'],v['status'],v['reason'],'r5',round(m['candidate_recall_at5'],3),'r5all',round(m['candidate_recall_at5_all_instances'],3),'iou',round(m['mask_iou_pos'],3),'ont',round(m['on_target_share_at85'],3),'fp',round(m['false_presence_absent_at85'],3),'skip',m['selection_skipped'])
    elif v['event'] not in ('train','recall_ceilings'): print(json.dumps(v)[:300])
PY
