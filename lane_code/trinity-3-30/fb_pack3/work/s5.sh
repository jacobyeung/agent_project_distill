cd /scratch/jjyeung/orch_n30/sb_own400 && grep -n "^ROOT\|^KIT\|def fresh\|def write_guard\|def digest\|def valid_grid" -A4 kit/core.py | head -50
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json
b=json.load(open('out/BARS_FROZEN.json'));ps=set();ps4=set();n=0
for r in b['captures']:
  try: ps.add(json.load(open(r['own544']['receipt']))['producer_sha256'])
  except Exception as e: pass
  try: ps4.add(json.load(open('in/own_400/native/probe/'+r['key']+'/PHASE_COMPLETE.json'))['producer_sha256']); n+=1
  except Exception as e: pass
print('544 producers',ps,'400 producers',ps4,'400 present',n,'captures',len(b['captures']),'gt_present',sum(r['gt_present'] for r in b['captures']))
P
