python3 -B -c "
import json,sys
for l in open(sys.argv[1],'rb'):
  r=json.loads(l); k=r['ranks'][0]
  if k.get('checkpoint_seconds',0)>0 or k.get('export_seconds',0)>0: print(r['step'], round(k['wall_seconds']), round(k.get('checkpoint_seconds',0)), round(k.get('export_seconds',0)))
" /project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/metrics_171377.jsonl
ls -la --time-style=+%FT%T /project/community/jjyeung/okh7/x_69d2930d/o/ | grep -i -E "gcs|done" | awk '{print $5,$6,$7}'
grep -n -i -E "export|m100|m200|gcs|upload|checkpoint" /project/community/jjyeung/okh7/x_69d2930d/o/171377.steps | tail -12 | cut -c1-200
