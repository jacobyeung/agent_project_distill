<!-- recovered by seal_plan: transcript=71f94277 line=16627 utc=2026-11-13T03:57:08.163Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/mdg_build/work/data/r7/x; ls r_119970 | head; for d in r_119970 r_119971; do f=$d/clips_c.jsonl; [ -f $f ] && { echo "== $f $(stat -c %s $f) B sha $(sha256sum $f | cut -c1-16)"; head -n 1 $f | /scratch/jjyeung/envs/p1cpu/bin/python -I -s -c "
import sys, json
r = json.loads(sys.stdin.readline())
print('top-level keys:', sorted(r.keys()))
for k in ('dataset','scene','canonical','scene_id','source','clip_id'):
    if k in r: print(k, '=', json.dumps(r[k])[:200])
p = r.get('provenance')
if isinstance(p, dict): print('provenance keys:', sorted(p.keys())); print('provenance.canonical =', json.dumps(p.get('canonical'))[:300])
"; }; done