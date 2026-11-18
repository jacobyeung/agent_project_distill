from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;O=W/'out';F=Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7')
A='/project/community/jjyeung/okh7/a15_cot_ap'+(O/'b1/TOKEN').read_text().strip()
B='/project/community/jjyeung/okh7/a15_cot_ap'+(O/'b2/TOKEN').read_text().strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for k,P in [('b1',A),('b2',B)]:
 d=O/k;token=(d/'TOKEN').read_text().strip();wall='05:00:00' if k=='b1' else '02:30:00'
 pre='#!/bin/bash\nset -euo pipefail\numask 077\nP='+P+'\n'
 place=pre+'''# D must identify the existing delivery directory, whose basename is opaque.
: "${D:?Set D to the existing opaque delivery directory}"
case "$D" in /project/community/jjyeung/okh7/a15_cot_ap*) ;; *) exit 1;; esac
'''+"printf '%s  %s\\n' "+sha(d/'1.tgz')+''' "$D/1.tgz" | sha256sum -c -
test ! -e "$P"
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);m=json.loads((p/'PACKAGE.json').read_text());v=json.loads((p/'0.json').read_text())
for name,digest in m['files'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
assert m['token']==v['token']
with tarfile.open(p/'0.tgz') as t:c=json.load(t.extractfile('9.json'))
assert hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()==v['plan_sha256']
b=c['export_binding'];assert b['run']=='673bc60f' and b['step']==200 and b['member_directory']=='m200'
assert json.loads((p/'a/1.json').read_text())=={'pending':True}
print('Metadata verified; export fill required')
PYCODE
'''
 (d/'o_place.sh').write_text(place)
 worker='''#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
A='''+A+'\nB='+B+'''
E=$A/a/e
OBJECT=q8/8865619b/673bc60f_m200.tar
DONE=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done
I=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs
'''
 if k=='b1':
  worker+='''test -f "$DONE"
test -f "$A/0.tgz"
test -f "$B/0.tgz"
test ! -e "$E"
mkdir -m 700 "$E"
cp "$DONE" "$E/5"
cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json" "$E/7"
cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json" "$E/8"
cp "$I/data_receipt.json" "$E/9"
/usr/bin/python3 -I -s -B - "$A" "$E" <<'PYCODE'
import hashlib,json,sys,tarfile,re
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
with tarfile.open(p/'0.tgz') as t:b=json.load(t.extractfile('9.json'))['export_binding']
f=(e/'5').read_text().split()
assert len(f)==3 and f[0]==b['object'] and f[1].isdigit() and int(f[1])>0 and re.fullmatch('[0-9a-f]{64}',f[2])
for key,name in [('config','7'),('receipt','8'),('data_receipt','9')]:
 assert hashlib.sha256((e/name).read_bytes()).hexdigest()==b['preparation_sha256'][key]
PYCODE
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"
done
'''
 else:worker+='''# No download path exists in B. A must finish and authenticate the shared parts first.
test -f "$E/10.json"
/usr/bin/python3 -I -s -B - "$A" "$E" <<'PYCODE'
import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2]);v=json.loads((e/'10.json').read_text())
assert v['passed'] is True
assert v['inputs_sha256']==hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest()
assert v['export_sha256']==hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest()
PYCODE
'''
 worker+='P='+P+'''
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" \
 --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" \
 --lineage SFT --step 200 --out "$P/a/export.json" --prep-tar "$P/a/6" \
 --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time '''+wall+'\n'
 if k=='b1':worker+='''/usr/bin/python3 -I -s -B - "$P" "$E" <<'PYCODE'
import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
v=dict(passed=True,inputs_sha256=hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest(),export_sha256=hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest())
(e/'10.json').write_text(json.dumps(v,sort_keys=True)+'\\n')
PYCODE
'''
 worker+="printf '%s\\n' 0 > \"$P/a/1.txt\"\n"
 pull=pre+'''test ! -e "$P/a/0.sh"
cat > "$P/a/0.sh" <<'SHELLCODE'
'''+worker+'''SHELLCODE
nohup bash "$P/a/0.sh" </dev/null >"$P/a/0.log" 2>&1 &
printf '%s\n' "$!" > "$P/a/0.txt"
'''
 (d/'o_pullfill.sh').write_text(pull)
 cpu=pre+'''test "$(cat "$P/a/1.txt")" = 0
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time '''+wall+'''
test ! -e "$P/a/4.txt"
test ! -e "$P/a/c"
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
 sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1 \
 --job-name=a15_cot_ap'''+token+''' --cpus-per-task=8 --mem=200G --time=04:00:00 \
 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue --chdir=/tmp \
 --output="$P/a/4.log" --error="$P/a/4.err" \
 --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$CPU_JOB" > "$P/a/4.txt"
'''
 (d/'o_cpucheck.sh').write_text(cpu)
 checks=json.loads((F/k/'READ_PLAN.json').read_text())['commands']['cpu_pass_check']
 sub=pre+'cd "$P"\n'+checks+'''\ntest ! -e "$P/a/8.txt"
squeue -u jjyeung -p general -h > "$P/a/9.txt"
test ! -s "$P/a/9.txt"
/usr/bin/python3 -I -s -B - <<'PYCODE'
import os
root='/project/community/jjyeung/okh7/ae71c903';total=0
for base,dirs,files in os.walk(root,followlinks=False):
 for name in files:
  p=os.path.join(base,name)
  if os.path.islink(p):raise ValueError('Unexpected pool symlink')
  total+=os.stat(p).st_size
  if total>75000000:raise ValueError('Return pool exceeds 75 MB')
print(total)
PYCODE
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time '''+wall+'''
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time '''+wall+''')
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
'''
 (d/'o_sub.sh').write_text(sub)
 fetch=pre+'''cd "$P"
JOB=$(cat "$P/a/8.txt")
[[ "$JOB" =~ ^[0-9]+$ ]]
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('''+repr(token)+'''+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
'''
 (d/'o_fetch.sh').write_text(fetch)
 # Full read authentication uses the input identity returned by the dispatched job.
 u=(F/k/'unpack_return.py').read_text().replace("inputs=json.loads((O/'inputs_tower.json').read_text())","inputs=json.loads((dest/'metadata/INPUTS.json').read_text())\n from orchard_h10.common import read_config\n from orchard_h10.export_pins import validate,admit\n admit(inputs,read_config(O/'package'),validate(json.loads((dest/'metadata/EXPORT_PIN.json').read_text())))")
 (d/'unpack_return.py').write_text(u)
 text='''# R1 step-200 operator commands

Package directory: `'''+P+'''`. All scripts run on the Orchard login node through the lane's existing `ossh.sh`. The scripts are inert deliverables; no placement, pull, CPU job, or GPU submission ran during this build.

Place A and B first. Run A's pull/fill and wait for `a/1.txt` to contain `0`; inspect `a/0.log` on failure. Then run B's pull/fill. B has no download command: it reuses A's verified four parts and rechecks their hashes. Neither script retries a failed transfer. The real S1 receipt must already exist at the bound preparation path.

```bash
# Set the delivery directory inside the script sent to Orchard; do not export a local path.
{ printf '%s\\n' 'D=/project/community/jjyeung/okh7/a15_cot_ap<delivery_hex>'; cat o_place.sh; } | bash ossh.sh 'bash -s'
bash ossh.sh 'bash -s' < o_pullfill.sh
# After fill succeeds:
bash ossh.sh 'bash -s' < o_cpucheck.sh
# After the CPU job completes successfully:
bash ossh.sh 'bash -s' < o_sub.sh
# After the GPU job finishes:
bash ossh.sh 'bash -s' < o_fetch.sh
```

The GPU script refuses unless the exact CPU receipt passes, the general queue for `jjyeung` is empty, and the return pool holds at most 75,000,000 bytes. It submits one GPU for `'''+wall+'''` and saves the job ID in `a/8.txt`. Run A and B sequentially. A local fixture receipt cannot authorize these commands.

Transfer `a/f/0.tgz` and `a/f/EXIT.json` through the lane's authorized transfer procedure into `'''+str(d/'f')+'''`. Then run locally:

```bash
cd '''+str(d)+'''
/scratch/jjyeung/envs/p1cpu/bin/python -B unpack_return.py --archive f/0.tgz --exit f/EXIT.json --out '''+str(d/'ret')+'''
```

After both returns are unpacked:

```bash
cd '''+str(O)+'''
OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B score_r1route.py --a b1/ret --b b2/ret --out scores
```

The scorer prints each baseline read and keeps missing items explicit. The camera denominator is always 450. Partial returns cannot certify H3. The room gate uses `mra_answer` against job 172456, separately for the 36 and 98 items.
'''
 (d/'OPERATIONS_R1ROUTE.md').write_text(text)
print(A,B)
