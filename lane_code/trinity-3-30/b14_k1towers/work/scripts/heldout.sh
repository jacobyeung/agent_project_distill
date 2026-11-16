G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; PY=/scratch/jjyeung/envs/planner_local_v1/bin/python; date -u
sha256sum k1towers/decide.py
test -e out/decide_heldout_once.json && { echo ALREADY_RUN; exit 1; }
$PY -B k1towers/decide.py harness/out_merged_mdp out/decide_heldout_once.json --heldout-go /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b14_k1towers/20261116T1453Z_ORCH_GO_heldout.md > out/decide_heldout_once.stdout 2>&1; echo EXIT $?
tail -1 out/decide_heldout_once.stdout
$PY - <<'PY'
import json
r = json.load(open('out/decide_heldout_once.json'))
for typ, t in r['tables']['heldout'].items():
    print('##', typ, 'heldout', t[next(iter(t))]['n_items'], 'items', t[next(iter(t))]['n_rooms'], 'rooms')
    for a, s in t.items():
        print(f"{a:24s} {s['mean']:7.2f} [{s['ci95'][0]:6.2f},{s['ci95'][1]:6.2f}] ref={s['refusals']}" + (f" | vs {s['vs']}: {s['diff']:+7.2f} [{s['diff_ci95'][0]:+7.2f},{s['diff_ci95'][1]:+7.2f}]" if 'diff' in s else ''))
print(json.dumps(r['decision'], indent=0))
print(json.dumps(r['verdict']))
PY
sha256sum out/decide_heldout_once.json
