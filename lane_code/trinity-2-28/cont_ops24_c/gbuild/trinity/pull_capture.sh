#!/bin/bash
# Run on trinity-3-30; the governor must register and resume the stopped group.
set -euo pipefail
umask 077
if [[ "${1:-}" == --inner ]]; then
    uri=$2; generation=$3; digest=$4; bytes=$5
    printf 'stopped_pgid=%s\n' "$$"
    kill -STOP -- "-$$"
    gcloud storage cat "$uri#$generation" | pv -q -L 8m | \
      ssh trinity-2-28.ib "bash --noprofile --norc -c 'set -euo pipefail; umask 077; mkdir -p /scratch/jjyeung/orch_n30/cont_ops24_c/cap; cd /scratch/jjyeung/orch_n30/cont_ops24_c/cap; set -C; cat > 0.gz; test \"\$(stat -c %s 0.gz)\" = $bytes; echo \"$digest  0.gz\" | sha256sum -c -'"
    exit
fi
[[ "$(hostname -s)" == trinity-3-30 ]]
[[ $# == 1 ]]
command -v gcloud >/dev/null
command -v pv >/dev/null
mapfile -t fields < <(python3 -B - "$1" <<'PY'
import json,re,sys
r=json.load(open(sys.argv[1]))
assert r['verified'] is True
assert re.fullmatch(r'gs://cmu-gpucloud-jjyeung/q8/ae71c903/[a-f0-9]{21}c/0.gz',r['uri'])
assert re.fullmatch(r'[0-9]+',str(r['generation']))
assert re.fullmatch(r'[0-9a-f]{64}',r['sha256'])
assert type(r['bytes']) is int and 0<r['bytes']<=1900000000
for k in ('uri','generation','sha256','bytes'):print(r[k])
PY
)
[[ ${#fields[@]} == 4 ]]
log="${1}.pull.log"
(set -C; : > "$log")
nohup setsid bash "$0" --inner "${fields[@]}" > "$log" 2>&1 < /dev/null &
printf 'Register stopped pipeline PGID %s with the IO governor; log: %s\n' "$!" "$log"
