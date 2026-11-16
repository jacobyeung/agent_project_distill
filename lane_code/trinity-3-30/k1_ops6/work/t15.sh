set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
echo "=== previous namespace diagnostic: deadline case failure"
D=evidence/batch_0803799192/deadline
ls $D | head -20
true
tail -c 300 $D/batch.log 2>/dev/null || true
echo "=== namespace success case depth records"
S=evidence/batch_0803799192/success
python3 -c "
import json; a=json.load(open('$S/a01.json')); print({k:v for k,v in a.items() if k.startswith('depth_')})
v=json.load(open('$S/VERIFIERS.json')); print([x for x in v if 'okit/in/cr' in json.dumps(x['role'])])"
stat -c '%h %n' stage_fixture.py
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
from pathlib import Path
import os
p = Path('stage_fixture.py'); assert os.stat(p).st_nlink == 1
t = p.read_text()
a1 = "    bwrap = dict(path=str(executable), bytes=7, sha256=H.sha(executable))\n"
assert t.count(a1) == 1
t = t.replace(a1, a1 + "    depth_raw = b'{\"schema\": \"rh-depth-fixture\"}\\n'\n"
    "    depth_file = objects / 'd.json'\n"
    "    depth_file.write_bytes(depth_raw)\n"
    "    depth = [dict(path=str(depth_file), bytes=len(depth_raw), sha256=hashlib.sha256(depth_raw).hexdigest(),\n"
    "                  logical_path='/scratch/jjyeung/a17/step/heads.json')]\n")
a2 = "                  bwrap=bwrap, fla=dict("
assert t.count(a2) == 1
t = t.replace(a2, "                  bwrap=bwrap, depth=depth, fla=dict(")
a3 = "        assert (stage / 'sj/a09/a.txt').read_bytes() == b'base'\n"
assert t.count(a3) == 1
t = t.replace(a3, a3 + "        assert (stage / 'sj/a17/step/heads.json').read_bytes() == depth_raw\n")
p.write_text(t)
print('patched stage_fixture')
PY
diff -u ../build/stage_fixture.py stage_fixture.py > evidence/B7_STAGE_FIXTURE.diff || true; cat evidence/B7_STAGE_FIXTURE.diff
/scratch/jjyeung/envs/p1cpu/bin/python -c "import ast;ast.parse(open('stage_fixture.py').read());print('syntax ok')"
mkdir -p out_r1 && for f in out/*; do mv "$f" out_r1/; done
cat > rh7d.sh <<'EOS'
#!/bin/bash
set -u
N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
P=/scratch/jjyeung/envs/p1cpu/bin/python
U=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
date -u +%FT%TZ > evidence/B7D_START.txt
export SLURM_JOB_ID=424242 HOME="$N/jt/home" XDG_CACHE_HOME="$N/jt/cache" TMPDIR="$N/jt/temp" TMP="$N/jt/temp" TEMP="$N/jt/temp" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
rc=0
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind "$N/jt" /tmp --bind "$N" /tmp/b7e31d84 --chdir /tmp/b7e31d84 --setenv HOME /tmp/home --setenv XDG_CACHE_HOME /tmp/cache --setenv TMPDIR /tmp/temp --setenv TMP /tmp/temp --setenv TEMP /tmp/temp --setenv HF_HOME /tmp/cache/hf --setenv TORCH_HOME /tmp/cache/torch --setenv TRITON_CACHE_DIR /tmp/cache/triton --die-with-parent "$U" -I -s -B /tmp/b7e31d84/rh_prepare.py > out/outer.log 2>&1 || rc=$?
echo $rc > evidence/B7D_OUTER.rc
nice -n 19 "$U" -I -s -B rh_prepare.py --collect "$rc" > evidence/B7D_COLLECT.log 2>&1; echo $? > evidence/B7D_COLLECT.rc
RUN=$(ls -td evidence/batch_* | head -1)
for c in $(ls -td evidence/batch_*/success | head -2); do
  nice -n 19 /usr/bin/bwrap --dev-bind / / --bind $N/$c/job_tmp/424242 /tmp --die-with-parent $P -I -s -B $N/ns_depth_check.py $N/$c > $N/$c/../NSDEPTH_$(basename $(dirname $c)).log 2>&1; echo "$c $?" >> evidence/B7D_NSDEPTH.rc
done
date -u +%FT%TZ > evidence/B7D_END.txt
EOS
chmod +x rh7d.sh; tmux new-session -d -s k1b7rh4 "bash $N/rh7d.sh" && echo TMUX_STARTED; date -u +%FT%TZ
