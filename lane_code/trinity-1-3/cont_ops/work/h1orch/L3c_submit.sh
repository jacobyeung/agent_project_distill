export PROOF_JOB=170669
export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28; K=$O/x_3fdda0fb
PROOF_JOB=${PROOF_JOB:?}
squeue -u jjyeung -n a15_cot_ap5ee9da63 -h | grep -q . && { echo "already queued"; exit 3; }
test ! -e $B/go.json || { echo "go.json exists"; exit 3; }
python3 - "$PROOF_JOB" <<'P'
import hashlib,json,sys
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28');K=Path('/project/community/jjyeung/okh7/x_3fdda0fb')
job=sys.argv[1]; pr=json.loads((K/'o'/(job+'.proof.json')).read_text())
assert pr['status']=='PASS' and pr['rc']==0, ('proof not PASS', pr.get('status'), pr.get('error'))
t=json.loads((B/'go.template.json').read_text());ids=json.loads((B/'ids.json').read_text())
man=hashlib.sha256((K/'SHA256SUMS.txt').read_bytes()).hexdigest();wr=hashlib.sha256((B/'jb.sh').read_bytes()).hexdigest()
assert man.startswith('661ccd85') and wr==t['wrapper_sha256'] and t['config_sha256']==ids['identity'] and t['admission_contract_sha256']==ids['contract']
t.update(manifest_sha256=man,production_go_granted=True,granted_by='orchestrator GO 0052Z (main returned advanced, INBOX 005156Z) + ruling 0211Z item 4 after review_h1sel GO and PASS CPU proof '+job+'; operator cont_ops10')
(B/'go.json').write_text(json.dumps(t,sort_keys=True));print('go.json written',man[:8],wr[:8])
P
[ $? -eq 0 ] || exit 4
PROOF_JOB=$PROOF_JOB bash $B/s.sh 2>&1 | grep -v ': OK$'
echo s_rc=${PIPESTATUS[0]}
squeue -u jjyeung -n a15_cot_ap5ee9da63 -o '%i %j %P %T %R'
