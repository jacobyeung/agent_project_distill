T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T; date -u +%TZ
sed -n 1,40p student_pilot/r2_scene_bindings.py; echo ----; sed -n 1,40p student_pilot/r2_withheld.py; sha256sum student_pilot/r2_withheld.json
python3 - <<'PY'
import json
d=json.load(open('student_pilot/r2_dev_merged.json')); print({k:(type(v).__name__, len(v) if hasattr(v,'__len__') else v) for k,v in d.items()}); print('rule',json.dumps(d.get('rule'))[:300], 'schema',d.get('schema'))
print('derivation' in d, json.dumps({k:d[k] for k in d if k not in ('aliases','canonical','natives','physical_groups','rooms')})[:600])
w=json.load(open('student_pilot/r2_withheld.json')); print('withheld', {k:(type(v).__name__, len(v) if hasattr(v,'__len__') else v) for k,v in w.items()} if isinstance(w,dict) else len(w))
PY
