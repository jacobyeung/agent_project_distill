set -euo pipefail
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7; B=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build; P=/scratch/jjyeung/envs/p1cpu/bin/python
cat > $N/depth_check.py <<'K1OPS6EOF'
"""K1 build7 rehearsal check: the staged depth files resolve exactly as carrier_c1.load_depth_stage1 reads them."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import job_support as H

S, R, NS, J = H.native()
case = Path(sys.argv[1])
ctx = json.loads((case / 'CONTEXT.json').read_text())
root = Path(ctx['stage'])
if ctx['mode'] == 'namespace':
    root = Path(ctx['tmp']) / root.relative_to('/tmp')
cfg = json.loads((HERE / 'packet/CONFIG.json').read_text())
manifest = json.loads((HERE / 'manifest_v2/a40fbc19.json').read_text())
out = dict(case=str(case), mode=ctx['mode'], stage=str(root), files=[])
mapping = {}
for i, item in enumerate(cfg['assets']['depth']):
    phys = NS.physical(root, item['logical_path'])
    row = dict(index=i, logical=item['logical_path'], physical=str(phys), is_file=phys.is_file())
    if phys.is_file():
        digest = H.sha(phys)
        row.update(bytes=phys.stat().st_size, sha256=digest, equals_production_pin=digest == item['sha256'])
    out['files'].append(row)
    mapping[item['logical_path']] = str(phys)
a01 = json.loads((case / 'a01.json').read_text())
out['a01_depth_records'] = {k: v for k, v in a01.items() if k.startswith('depth_')}
verifiers = json.loads((case / 'VERIFIERS.json').read_text())
paths = [d['path'] for d in cfg['assets']['depth']]
out['depth_transport_verifiers'] = [v for v in verifiers if any(p in json.dumps(v['role']) for p in paths)]
gcfg = manifest['gpu']['config']
staged_cfg = NS.physical(root, gcfg['path'])
out['prepared_config'] = dict(path=gcfg['path'], staged=str(staged_cfg), equals_pin=H.sha(staged_cfg) == gcfg['sha256'])
depth_init = json.loads(staged_cfg.read_text())['depth_init']
out['depth_init'] = depth_init
tree = NS.physical(root, cfg['assets']['tree_root'])
sys.path.insert(0, str(tree))
from student_pilot.p3_provenance import load, pinned
import student_pilot.p3_provenance as prov
out['p3_provenance_file'] = prov.__file__
import phase_worker as PW
with PW.metadata_mapping(mapping):
    artifact = load(pinned(depth_init))
    out['carrier_c1_692_pinned_depth_init'] = 'passed'
    out['schema_and_backing_ok'] = (artifact.get('schema') == 'p3-head-artifact-v1'
                                    and artifact.get('feature_backing') == 'decoupled_vc')
    for name, pin in (('encoder_copy.weights', artifact['encoder_copy']['weights']), ('weights', artifact['weights'])):
        row = dict(path=pin['path'], resolves_to_staged_file=Path(pin['path']).is_file(),
                   staged_as=mapping.get(pin['path']))
        try:
            pinned(pin)
            row['pinned'] = 'passed'
        except ValueError as error:
            row['pinned'] = 'raised on stand-in bytes (expected in rehearsal): ' + str(error)[:60]
        out[name] = row
H.dump(case / 'DEPTH_CHECK.json', out)
print(json.dumps(out, indent=1))
K1OPS6EOF
cat > $N/payload_diff.py <<'K1OPS6EOF'
import base64, hashlib, io, json, re, sys, tarfile
def payload(sh):
    t = open(sh).read()
    b64 = re.search(r"b64decode\('([A-Za-z0-9+/=]+)',validate=True\)", t).group(1)
    sha = re.search(r"hexdigest\(\)!='([0-9a-f]{64})'", t).group(1)
    raw = base64.b64decode(b64)
    assert hashlib.sha256(raw).hexdigest() == sha
    tf = tarfile.open(fileobj=io.BytesIO(raw))
    files = {m.name: tf.extractfile(m).read() for m in tf.getmembers()}
    return files, t.replace(b64, 'B64').replace(sha, 'SHA'), sha
old, ot, osha = payload(sys.argv[1]); new, nt, nsha = payload(sys.argv[2])
res = dict(old_payload_sha=osha, new_payload_sha=nsha, members_old=len(old), members_new=len(new),
           added=sorted(set(new) - set(old)), removed=sorted(set(old) - set(new)),
           changed=sorted(k for k in old if k in new and old[k] != new[k]),
           launcher_text_equal_except_payload_and_sha=ot == nt,
           a_json_equal=old.get('a.json') == new.get('a.json'))
print(json.dumps(res, indent=1))
K1OPS6EOF
cat > $N/rh7.sh <<'K1OPS6EOF'
#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$N/evidence/b7_tmp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%FT%TZ > evidence/B7_RH_START.txt
nice -n 19 $P -B rh_batch.py --diagnostic-python $P > evidence/B7_MAPPED.log 2>&1; echo $? > evidence/B7_MAPPED.rc
RUN=$($P -c "import json;print(json.load(open('evidence/BATCH_LATEST.json'))['run'])"); echo $RUN > evidence/B7_MAPPED.run
nice -n 19 $P -B depth_check.py $RUN/success > evidence/B7_DEPTH_MAPPED.log 2>&1; echo $? > evidence/B7_DEPTH_MAPPED.rc
date -u +%FT%TZ > evidence/B7_MAPPED_END.txt
SLURM_JOB_ID=7000071 nice -n 19 $P -B rh_batch.py --namespace --diagnostic-python $P --cases success > evidence/B7_NS.log 2>&1; echo $? > evidence/B7_NS.rc
RUN=$($P -c "import json;print(json.load(open('evidence/BATCH_LATEST.json'))['run'])"); echo $RUN > evidence/B7_NS.run
nice -n 19 $P -B depth_check.py $RUN/success > evidence/B7_DEPTH_NS.log 2>&1; echo $? > evidence/B7_DEPTH_NS.rc
date -u +%FT%TZ > evidence/B7_RH_END.txt
K1OPS6EOF
cd $N && chmod +x rh7.sh && $P -B payload_diff.py evidence/B7_batch_before.sh packet/a7e31d84.sh | tee evidence/B7_PAYLOAD_DIFF.json
echo "--- run_rh.sh"; cat $B/rh/run_rh.sh 2>&1 | head -40
tmux new-session -d -s k1b7rh "bash $N/rh7.sh" && echo TMUX_STARTED; date -u +%FT%TZ
