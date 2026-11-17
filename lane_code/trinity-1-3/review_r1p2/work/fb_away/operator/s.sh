#!/bin/bash
set -euo pipefail
export TZ=UTC
umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"
BUN=/project/community/jjyeung/okh7/i_011a9ccb
KH=/project/community/jjyeung/okh7/x_011a9ccb
private_dir "$BUN"
private_dir "$KH"
cd "$BUN"
sha256sum -c sums.txt
# The separate approval record is supplied by the operator, never inferred from 4.json.
python3 -B - "$KH" "$BUN" <<'P'
import hashlib,json,sys,os,re
from pathlib import Path
k,b=map(Path,sys.argv[1:]);go=json.loads((b/'go.json').read_text());ids=json.loads((b/'ids.json').read_text())
assert go.get('production_go_granted') is True and go.get('config_sha256')==ids['identity'] and go.get('admission_contract_sha256')==ids['contract'] and go.get('wrapper_sha256')==hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest()
assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
job=os.environ.get('PROOF_JOB','')
assert re.fullmatch('[1-9][0-9]*',job), 'PROOF_JOB must identify the completed CPU proof'
proof=json.loads((k/'o'/(job+'.proof.json')).read_text())
launch=json.loads((k/'k/launch.json').read_text())
assert proof.get('status')=='PASS' and proof.get('rc')==0 and proof.get('job')==job
assert proof.get('config_identity')==ids['identity'] and proof.get('contract_sha256')==ids['contract']
assert proof.get('config')==launch['config'] and proof.get('manifest_sha256')==go['manifest_sha256']
assert proof.get('wrapper_sha256')==go['wrapper_sha256'] and proof.get('cuda_visible_devices')==''
assert proof.get('effective_config_verified') is True and proof.get('first_batch_executed') is False
assert proof.get('training_executed') is False and proof.get('admission_result', dict()).get('status')=='PREPARED'
assert proof.get('prepared_seals') and proof.get('real_job_reuse') is False
for name in ('disk_plan','routing_selection','empty_root','temporary_paths','runtime_binaries','directory_modes','loader_audit','required_families'):
 assert proof.get('checks',{}).get(name,{}).get('status')=='PASS', name

sys.path.insert(0,str(k/'b'));import a;a.main(k)
P
TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_ap16d2e04e -o /dev/null -e "$KH/o/%j.err"   -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
