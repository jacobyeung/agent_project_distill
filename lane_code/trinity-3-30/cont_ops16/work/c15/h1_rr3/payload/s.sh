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
BUN=/project/community/jjyeung/okh7/i_1be16f28
KH=/project/community/jjyeung/okh7/x_4b3114cf
private_dir "$BUN"
private_dir "$KH"
cd "$BUN"
sha256sum -c sums.txt
# The separate approval record is supplied by the operator, never inferred from 4.json.
python3 -B - "$KH" "$BUN" <<'P'
import hashlib,json,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:]);go=json.loads((b/'go.json').read_text());ids=json.loads((b/'ids.json').read_text())
assert go.get('production_go_granted') is True and go.get('config_sha256')==ids['identity'] and go.get('admission_contract_sha256')==ids['contract'] and go.get('wrapper_sha256')==hashlib.sha256((b/'jb.sh').read_bytes()).hexdigest()
assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
sys.path.insert(0,str(k/'b'));import a;a.main(k)
P
TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_ap5ee9da63 -o /dev/null -e "$KH/o/%j.err"   -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
