R=/scratch/jjyeung/orch_n30
date -u +%TZ; tail -2 $R/sb_queue/codexq.log; pgrep -f "codex_dispatch.sh implement $R/sb_" -a | grep -o "label [a-zA-Z0-9_]*" | sort -u | tr "\n" " "; echo
echo == f64 procs; pgrep -af "agent -p" | grep -c . ; for s in sb_f64 sb_recrev sb_arev2 sb_brev3 sb_afrev; do echo "$s $(stat -c %y $R/$s/cursor.log | cut -c12-19) $(wc -c < $R/$s/cursor.log)"; done; ls -lt --time-style=+%H:%M $R/sb_f64 $R/sb_f64/out | head -12
echo == handoff; cat $R/sb_rowA/out/HANDOFF_cont_ops18.md | head -60
echo == heldout; cd $R/sb_rowA/out && /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json,collections
for f in ['HELDOUT_CAMERA_ITEMS.json','HELDOUT_FREEZE.json','HELDOUT_CAMERA_TWINS.json']:
    d=json.load(open(f))
    print(f,type(d).__name__, list(d.keys())[:15] if isinstance(d,dict) else len(d))
d=json.load(open('HELDOUT_CAMERA_ITEMS.json'))
items=d if isinstance(d,list) else next(v for v in d.values() if isinstance(v,list))
print(len(items)); print(json.dumps(items[0])[:900])
c=collections.Counter()
for it in items:
    c[tuple(str(it.get(k)) for k in ('question_type','type','source_set','set','wording_id','origin') if k in it)]+=1
for k,v in sorted(c.items())[:40]: print(v,k)
PY
