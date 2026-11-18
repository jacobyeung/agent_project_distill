#!/bin/bash
# RUN ONLY AFTER A WRITTEN ORCH GO. Usage via ossh: timeout 300 bash ossh.sh 'bash -s -- <PROOF_JOB> <GO_SHA>' < go_submit_a5dc8f30.sh
# GO_SHA = sha256 hex of the ORCH GO event file (computed on Trinity), so no free text reaches Orchard argv.
set -Eeuo pipefail; umask 077; export TZ=UTC
PROOF_JOB=${1:-}; GO_SHA=${2:-}
[[ "$PROOF_JOB" =~ ^[1-9][0-9]*$ && "$GO_SHA" =~ ^[0-9a-f]{64}$ ]] || { echo 'usage: <PROOF_JOB> <GO_SHA (64 hex)>'; exit 2; }
O=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/submit_p5_9t9h3zy9/remote; BUN=$O/i_69d2930d; KH=$O/x_69d2930d; JN=a15_cot_ap673bc60f
cd "$BUN"
printf '%s  %s\n' 6fac31e33a7ba701f504c5b6a70b5d2d64da8e18007e87189ce7fefc2c137530 s.sh c3ed4fe38542a553244c270662ddc952a86b384bb479b7229de5e16f0b4bf686 sums.txt b6a1e4c8f4c0a8fce029233575d082fae69ba018a311288dc8391493efa4648f jb.sh | sha256sum -c --quiet
sha256sum -c --quiet sums.txt
squeue -u $USER -o '%i|%j|%P|%T|%R'
q=$(squeue -u $USER -h -p advanced -n $JN -o '%i|%T'); a=$(sacct -X -n -P -S 2026-11-17 -r advanced --name $JN -o JobID,State 2>/dev/null || true)
[[ -z "$q" && -z "$a" ]] || { echo "REFUSED: a training job named $JN already exists on advanced: ${q}${a}"; exit 5; }
python3 -I -B - "$KH" "$BUN" "$GO_SHA" <<'PY'
import hashlib,json,sys
from pathlib import Path
k,b,ref=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
ids=json.loads((b/'ids.json').read_text())
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
        wrapper_sha256=hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority='sha256:'+ref)
data=json.dumps(go,sort_keys=True); p=b/'go.json'
if p.exists() or p.is_symlink():
    if p.is_symlink() or p.read_text()!=data: sys.exit('REFUSED: existing go.json differs; inspect, never overwrite')
    print('go.json exists and is byte-equal; reusing')
else:
    with p.open('x') as f: f.write(data)
    p.chmod(0o600); print('go.json written', go['config_sha256'][:8])
PY
PROOF_JOB=$PROOF_JOB bash s.sh
