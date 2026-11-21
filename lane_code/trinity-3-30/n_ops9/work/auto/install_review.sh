#!/bin/bash
# n_ops9: install the reviewer's review.json byte-exact at X/n_r/review.json (dir 0700, file 0600, O_EXCL, sha256 after placement). ONE ossh call.
# usage: install_review.sh /path/to/review.json   (wait for a watcher line in mon/hist.txt, sleep 62 s, then run)
set -euo pipefail; F=${1:?review.json}; [[ -s $F ]] || { echo "REFUSED: $F empty"; exit 3; }
python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$F" || { echo "REFUSED: not JSON"; exit 3; }
H=$(sha256sum "$F" | cut -d' ' -f1); P64=$(base64 -w0 "$F"); I=$(mktemp /scratch/jjyeung/orch_n30/n_ops9/work/auto/inst_rev.XXXX.sh)
cat > $I <<IN
set -euo pipefail; umask 077; D=/project/community/jjyeung/okh7/x_22c714e1/n_r; T=\$D/review.json
[[ -e \$T || -L \$T ]] && { echo "REFUSED: \$T exists"; exit 3; }
[[ -d \$D ]] || mkdir -m 700 \$D; [[ -d \$D && ! -L \$D ]] || { echo "REFUSED: n_r not a dir"; exit 3; }; chmod 700 \$D
python3 -B - <<'PY'
import base64,hashlib,os
raw=base64.b64decode("$P64"); assert hashlib.sha256(raw).hexdigest()=="$H"
fd=os.open("/project/community/jjyeung/okh7/x_22c714e1/n_r/review.json",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,raw); os.close(fd)
PY
echo "$H  \$T" | sha256sum -c --quiet && echo "PASS installed \$T sha256=$H mode \$(stat -c %a \$T) dir \$(stat -c %a \$D)"
ls -la \$D
IN
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < $I 2>&1 | tee $I.out
