#!/bin/bash
# Step 8b-11 builder: writes L2.sh (0600, contains session URIs; never print it) for one ossh call. Run after L1_mint.sh.
set -euo pipefail; umask 077
W=/scratch/jjyeung/orch_n30/cont_ops/work; S=$W/h1orch/sess_17c4ffa4.json; L=$W/h1orch/L2.sh
test -f $S && test ! -e $L
H=$(sha256sum $S | cut -d' ' -f1)
{ cat <<HDR
export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=\$O/i_1be16f28; K=\$O/x_4b3114cf
date -u +%TZ; hostname
squeue -u jjyeung -o '%i %j %P %T %R' | head -30
df -B1G --output=avail /project/community/jjyeung | tail -1 | awk '{print "project_free_GB",\$1; if (\$1<140) {print "LOW_SPACE"; exit 3}}' || exit 3
test ! -e \$K/sess.json || { echo "sess.json exists"; exit 3; }
test ! -e \$B/go.json || { echo "go.json exists"; exit 3; }
cat > \$K/sess.json <<'EOF_S'
HDR
cat $S
cat <<TAIL
EOF_S
chmod 600 \$K/sess.json
[ "\$(sha256sum < \$K/sess.json | cut -d' ' -f1)" = "$H" ] || { echo "sess hash mismatch"; exit 3; }
echo "sess.json installed 600 44 keys"
python3 - <<'P'
import hashlib,json
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28');K=Path('/project/community/jjyeung/okh7/x_4b3114cf')
t=json.loads((B/'go.template.json').read_text());ids=json.loads((B/'ids.json').read_text())
man=hashlib.sha256((K/'SHA256SUMS.txt').read_bytes()).hexdigest();wr=hashlib.sha256((B/'jb.sh').read_bytes()).hexdigest()
assert man.startswith('bb9914ca') and wr==t['wrapper_sha256'] and t['config_sha256']==ids['identity'] and t['admission_contract_sha256']==ids['contract']
t.update(manifest_sha256=man,production_go_granted=True,granted_by='orchestrator GO (main returned GPUs); operator cont_ops9')
(B/'go.json').write_text(json.dumps(t,sort_keys=True));print('go.json written',man[:8],wr[:8])
P
TAIL
} > $L
chmod 600 $L; ls -la $L | awk '{print $1,$5}'
