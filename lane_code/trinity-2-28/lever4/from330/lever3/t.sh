summary=$(/usr/bin/python3 - /dev/shm/lever3/fake.json <<'PY'
import json,sys
try: r=json.load(open(sys.argv[1]))
except Exception as e: print('SCOREFAIL',e); sys.exit()
if not r.get('complete'): print('INCOMPLETE',json.dumps(r)[:600]); sys.exit()
f=lambda k:f"{100*r[k]['rate']:.1f}% [{100*r[k]['ci95'][0]:.1f}, {100*r[k]['ci95'][1]:.1f}]"
print('PASS' if r['REVSI']['rate']>=.95 else 'UNDER', f"ORIG {f('ORIG')}; REVSI {f('REVSI')}; REVSI-ORIG {f('REVSI_minus_ORIG')} (pp); pairs {r['pairs']}, rooms {r['rooms']}, {r['draws']} paired room draws, seed {r['seed']}; gate: {r['gate']}; other calls {json.dumps(r.get('other_calls'))[:300]}")
PY
)
echo "$summary"
