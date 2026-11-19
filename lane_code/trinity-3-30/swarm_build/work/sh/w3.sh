R=/scratch/jjyeung/orch_n30
date -u +%TZ
for t in sb_fpjoin sb_rowLR; do d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*_$t | tail -1); echo "== $t"; grep $t $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log | tail -1; cat $d/final_message.md | head -c 1500; echo; done
echo == FPJOIN; head -80 $R/sb_framepool/out/FPJOIN_REPORT.md
echo == LR; head -40 $R/sb_rowLR/out/REPORT.md
cd $R/sb_rowA/out && /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
d=json.load(open('HELDOUT_CAMERA_ITEMS.json')); print('per_type',d['per_type'],'status',d['status'])
t=json.load(open('HELDOUT_CAMERA_TWINS.json')); print('assignment',str(t['assignment'])[:300]); print('per_wording',json.dumps(t['per_wording'])[:1500]); print('native_tasks',str(t['native_tasks'])[:200])
print(json.dumps(t['twins'][0] if isinstance(t['twins'],list) else list(t['twins'].items())[0])[:500])
PY
sha256sum HELDOUT_CAMERA_ITEMS.json HELDOUT_CAMERA_TWINS.json HELDOUT_NATIVE_TASKS.jsonl WORDINGS.json SCORER_PATCH/placement.patch 2>/dev/null; ls SCORER_PATCH
