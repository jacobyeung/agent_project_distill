#!/bin/bash
# RUN ONLY AFTER A WRITTEN ORCH GO. Usage via ossh: timeout 300 bash ossh.sh 'bash -s -- <PROOF_JOB> <GO_EVENT_BASENAME>' < go_submit_69d2930d.sh
set -Eeuo pipefail; umask 077; export TZ=UTC
PROOF_JOB=$1; GO_REF=$2
[[ "$PROOF_JOB" =~ ^[1-9][0-9]*$ && -n "$GO_REF" ]] || { echo 'usage: <PROOF_JOB> <GO_REF>'; exit 2; }
O=/project/community/jjyeung/okh7; BUN=$O/i_69d2930d; KH=$O/x_69d2930d
[[ ! -e "$BUN/go.json" ]] || { echo 'REFUSED: go.json exists; inspect, never overwrite'; exit 3; }
squeue -u $USER -o '%i|%j|%P|%T|%R'
python3 -I -B - "$KH" "$BUN" "$GO_REF" <<'PY'
import hashlib,json,sys
from pathlib import Path
k,b,ref=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
ids=json.loads((b/'ids.json').read_text())
go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
        wrapper_sha256=hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest(),authority=ref)
p=b/'go.json'
with p.open('x') as f: json.dump(go,f,sort_keys=True)
p.chmod(0o600); print('go.json written', go['config_sha256'][:8])
PY
cd "$BUN"; PROOF_JOB=$PROOF_JOB bash s.sh
