K=/project/community/jjyeung/okh7; cd $K
for f in x_*/runs/*/metrics_*.jsonl; do echo "== $f"; nice -n 10 python3 -I -s -B - "$f" <<'PY'
import json,sys
last=None
for line in open(sys.argv[1]):
    try: r=json.loads(line)
    except Exception: continue
    rk=r.get('ranks') or [r]
    def mx(k):
        v=[x.get(k) for x in rk if isinstance(x.get(k),(int,float))]
        return max(v) if v else 0
    c,e=mx('checkpoint_seconds'),mx('export_seconds'); last=r.get('step')
    if c>0 or e>0: print(r.get('step'),'ckpt_s',round(c,1),'export_s',round(e,1))
print('last_step',last)
PY
done 2>&1 | head -150
