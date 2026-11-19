cd /lab_data/tarrlab/jacoby/agent_project/aws_evac || exit 1
python3 - <<'PY'
import json
d=json.load(open('_direct/map/17eedd296fe8.json'))
m=d['manifest']; print(type(m).__name__, (len(m) if hasattr(m,'__len__') else ''))
print(json.dumps(m)[:800])
o=json.load(open('_direct/ok/17eedd296fe8.json')); print(json.dumps(o)[:1500])
PY
P='97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad'
G=/lab_data/tarrlab/jacoby/gcs_evac_20261111
for f in $(grep -l -E "$P" $G/_receipts/*.json 2>/dev/null); do echo "== $f"; head -c 500 $f; echo; done | head -60
