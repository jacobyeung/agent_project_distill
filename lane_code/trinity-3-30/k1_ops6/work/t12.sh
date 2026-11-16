set -euo pipefail
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cat > $N/ns_depth_check.py <<'K1OPS6EOF'
"""Resolve the depth pins inside the job's own bwrap namespace (stage_job/NS.namespace binds) on a rehearsal stage root.
Omits only the pool and gcloud binds (return transport), which play no part in /scratch/fsw resolution."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import job_support as H
S, R, NS, J = H.native()
case = Path(sys.argv[1])
ctx = json.loads((case / 'CONTEXT.json').read_text())
# Run under an outer bwrap that binds the case's job_tmp/424242 onto /tmp, as the job's private /tmp.
root = Path('/tmp') / Path(ctx['stage']).name
assert root.is_dir(), root
config = json.loads((root / 'a03.json').read_text())
manifest = json.loads((HERE / 'manifest_v2/a40fbc19.json').read_text())
argv = NS.namespace(root, config)
argv[0] = '/usr/bin/bwrap'  # the staged copy under root is the same host binary in this rehearsal
for logical in ('/scratch/jjyeung/envs/p1cpu', '/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu'):
    NS.physical(root, logical).mkdir(parents=True, exist_ok=True)
    argv += ['--ro-bind', logical, logical]
check = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, %r)
from student_pilot.p3_provenance import load, pinned, sha256
import student_pilot.p3_provenance as P
gpu = %r
cfg = load(pinned(gpu))
pin = cfg['depth_init']
art = load(pinned(pin))
out = dict(inside_namespace=True, p3_provenance=P.__file__, prepared_config=gpu['path'], depth_init=pin,
           carrier_c1_692=('passed' if art.get('schema') == 'p3-head-artifact-v1' and art.get('feature_backing') == 'decoupled_vc' else 'schema differs'))
for name, w in (('encoder_copy.weights', art['encoder_copy']['weights']), ('weights', art['weights'])):
    p = Path(w['path'])
    out[name] = dict(path=w['path'], is_file=p.is_file(), bytes=p.stat().st_size if p.is_file() else None,
                     sha_equals_pin=(sha256(p) == w['sha256']) if p.is_file() else None)
print(json.dumps(out))
''' % (config['assets']['tree_root'], manifest['gpu']['config'])
cmd = argv + ['/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-c', check]
H.dump(case / 'NS_DEPTH_ARGV.json', cmd)
done = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
result = dict(returncode=done.returncode, stdout=done.stdout.strip(), stderr=done.stderr.strip()[-1500:], stage=str(root))
H.dump(case / 'NS_DEPTH_CHECK.json', result)
print(json.dumps(result, indent=1))
raise SystemExit(done.returncode)
K1OPS6EOF
cat > $N/rh7c.sh <<'K1OPS6EOF'
#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
P=/scratch/jjyeung/envs/p1cpu/bin/python
U=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
date -u +%FT%TZ > evidence/B7C_START.txt
MR=$(cat evidence/B7_MAPPED.run)/success
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind $MR/job_tmp/424242 /tmp --die-with-parent $P -I -s -B $N/ns_depth_check.py $MR > evidence/B7_NSDEPTH_MAPPED.log 2>&1; echo $? > evidence/B7_NSDEPTH_MAPPED.rc
# Namespace rehearsal exactly as run_rh.sh does it on trinity-1-3, with build7 as the package root.
mkdir -p jt/home jt/cache jt/temp jt/job_tmp/424242 out
export SLURM_JOB_ID=424242 HOME="$N/jt/home" XDG_CACHE_HOME="$N/jt/cache" TMPDIR="$N/jt/temp" TMP="$N/jt/temp" TEMP="$N/jt/temp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
rc=0
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind "$N/jt" /tmp --bind "$N" /tmp/b7e31d84 --chdir /tmp/b7e31d84 --setenv HOME /tmp/home --setenv XDG_CACHE_HOME /tmp/cache --setenv TMPDIR /tmp/temp --setenv TMP /tmp/temp --setenv TEMP /tmp/temp --setenv HF_HOME /tmp/cache/hf --setenv TORCH_HOME /tmp/cache/torch --setenv TRITON_CACHE_DIR /tmp/cache/triton --die-with-parent "$U" -I -s -B /tmp/b7e31d84/rh_prepare.py > out/outer.log 2>&1 || rc=$?
echo $rc > evidence/B7C_OUTER.rc
nice -n 19 "$U" -I -s -B rh_prepare.py --collect "$rc" > evidence/B7C_COLLECT.log 2>&1; echo $? > evidence/B7C_COLLECT.rc
date -u +%FT%TZ > evidence/B7C_END.txt
K1OPS6EOF
R=$(cat $N/evidence/B7_NS2.run); echo "--- NS2 batch.log tail"; tail -c 1200 $R/success/batch.log 2>/dev/null; ls $R/success | head
chmod +x $N/rh7c.sh; tmux new-session -d -s k1b7rh3 "bash $N/rh7c.sh" && echo TMUX_STARTED; date -u +%FT%TZ
