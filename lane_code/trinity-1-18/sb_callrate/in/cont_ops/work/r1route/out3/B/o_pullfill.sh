#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85
test ! -e "$P/a/0.sh"
cat > "$P/a/0.sh" <<'SHELLCODE'
#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
A=/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a
B=/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85
E=$A/a/e
OBJECT=q8/8865619b/673bc60f_m200.tar
DONE=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m200.done
I=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs
# No download path exists in B. A must finish and authenticate the shared parts first.
test -f "$E/10.json"
/usr/bin/python3 -I -s -B - "$A" "$E" <<'PYCODE'
import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2]);v=json.loads((e/'10.json').read_text())
assert v['passed'] is True
assert v['inputs_sha256']==hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest()
assert v['export_sha256']==hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest()
PYCODE
P=/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3"  --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9"  --lineage SFT --step 200 --out "$P/a/export.json" --prep-tar "$P/a/6"  --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
printf '%s\n' 0 > "$P/a/1.txt"
SHELLCODE
nohup bash "$P/a/0.sh" </dev/null >"$P/a/0.log" 2>&1 &
printf '%s
' "$!" > "$P/a/0.txt"
