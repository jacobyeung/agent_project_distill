#!/bin/bash
# n_ops8: mint 104 per-allocation create-only sessions for kit 24m4z (k/y.json objects + .j<JOB> + .partNN-of-04) and install them
# usage: sess_job.sh JOB [mint|install|all|names] [DEST_DIR (default X/n_s)] [YJSON]
# Never prints session URIs. Installer output = PASS line + listing only.
set -euo pipefail; umask 077
J=${1:?job}; MODE=${2:-all}; D=${3:-/project/community/jjyeung/okh7/x_22c714e1/n_s}; G=/scratch/jjyeung/orch_n30/n_ops8/work/gcs; Y=${4:-$G/y_24m4z.json}
PY=/scratch/jjyeung/envs/p1cpu/bin/python; MINT=/scratch/jjyeung/orch_n30/n_ops1/work/gcs/mint_n.py
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
[[ $J =~ ^[0-9]+$ ]] || { echo "REFUSED: job id not numeric"; exit 3; }
NF=$G/names_$J.json; S=$G/private/sess_$J.json; I=$G/private/install_$J.sh
if [[ $MODE == names || $MODE == mint || $MODE == all ]]; then
  [[ -e $NF ]] || $PY - "$Y" "$J" "$NF" <<'PY'
import json,base64,hashlib,sys
d=json.load(open(sys.argv[1])); raw=base64.b64decode(d['payload']); assert hashlib.sha256(raw).hexdigest()==d['sha256']
o=json.loads(raw)['objects']; n=[v+'.j'+sys.argv[2]+'.part%02d-of-04'%i for v in o.values() for i in range(4)]
assert len(n)==len(set(n))==4*len(o); json.dump(n,open(sys.argv[3],'x'),indent=1); print('names',len(n),n[0],n[-1])
PY
fi
if [[ $MODE == mint || $MODE == all ]]; then
  $PY $MINT mint "$S" "$NF" | tee $G/mint_$J.out
fi
if [[ $MODE == install || $MODE == all ]]; then
  [[ -s $S && ! -e $I ]] || { echo "REFUSED: no sessions or installer exists"; exit 3; }
  H=$(sha256sum "$S" | cut -d' ' -f1); P64=$(base64 -w0 "$S"); T=$D/sess_$J.json
  ( umask 077; cat > $I <<IN
set -euo pipefail; umask 077
D=$D; T=$T
[[ -e \$T || -L \$T ]] && { echo "REFUSED: \$T exists"; exit 3; }
[[ -d \$D ]] || mkdir -m 700 \$D
[[ -d \$D && ! -L \$D ]] || { echo "REFUSED: dest not a dir"; exit 3; }
chmod 700 \$D
python3 -B - <<'PY'
import base64,hashlib,os
raw=base64.b64decode("$P64")
assert hashlib.sha256(raw).hexdigest()=="$H"
fd=os.open("$T",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
os.write(fd,raw);os.close(fd)
PY
echo "$H  \$T" | sha256sum -c --quiet && echo "PASS installed \$T sha256=$H mode \$(stat -c %a \$T) size \$(stat -c %s \$T) dir \$(stat -c %a \$D); contents withheld"
ls -la \$D
IN
  )
  timeout 300 bash $B/tools/ossh.sh 'bash -s' < $I 2>&1 | sed -E 's#https://[^ "]*#<URL>#g' | tee $G/install_$J.out
fi
