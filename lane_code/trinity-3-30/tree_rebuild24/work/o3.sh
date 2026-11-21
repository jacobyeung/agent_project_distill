export TZ=UTC; K=/project/community/jjyeung/okh7; cd $K; ls -l --time-style=+%FT%H:%M x_*/runs/*/metrics_*.jsonl 2>/dev/null | awk '{print $5,$6,$7}'
for f in x_*/runs/*/metrics_*.jsonl; do echo "== $f"; nice -n 10 python3 -I -s -B - "$f" <<'PY'
import json,sys
for line in open(sys.argv[1]):
    try: r=json.loads(line)
    except Exception: continue
    c=r.get('checkpoint_seconds') or 0; e=r.get('export_seconds') or 0
    if (isinstance(c,(int,float)) and c>0) or (isinstance(e,(int,float)) and e>0):
        print(r.get('step'), 'ckpt_s', c, 'export_s', e, 'rank', r.get('rank'), {k:r[k] for k in r if 'byte' in k.lower() or 'stop' in k.lower()} )
PY
done 2>&1 | head -120
