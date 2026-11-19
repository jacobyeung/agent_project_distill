#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apf9bae9efe2bd5
test ! -e "$P/a/0.sh"
cat > "$P/a/0.sh" <<'SHELLCODE'
#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
A=/project/community/jjyeung/okh7/a15_cot_apf9bae9efe2bd5
E=$A/a/e
OBJECT=q8/8865619b/673bc60f_m400.tar
DONE=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m400.done
I=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f/inputs
test -f "$DONE"
test -f "$A/0.tgz"
test ! -e "$E"
mkdir -m 700 "$E"
cp "$DONE" "$E/5"
cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json" "$E/7"
cp "$I/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/s1_receipt.json" "$E/8"
cp "$I/data_receipt.json" "$E/9"
/usr/bin/python3 -I -s -B - "$A" "$E" <<'PYCODE'
import hashlib,json,sys,tarfile,re
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
with tarfile.open(p/'0.tgz') as t:b=json.load(t.extractfile('9.json'))['export_binding']
f=(e/'5').read_text().split()
assert len(f)==3 and f[0]==b['object'] and f[1].isdigit() and int(f[1])>0 and re.fullmatch('[0-9a-f]{64}',f[2])
assert int(f[1])==21583040512 and f[2]=='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'Completion receipt differs from the reviewed export'
for key,name in [('config','7'),('receipt','8'),('data_receipt','9')]:
 assert hashlib.sha256((e/name).read_bytes()).hexdigest()==b['preparation_sha256'][key]
PYCODE
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"
done
P=/project/community/jjyeung/okh7/a15_cot_apf9bae9efe2bd5
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3"  --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9"  --lineage SFT --step 400 --out "$P/a/export.json" --prep-tar "$P/a/6"  --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
/usr/bin/python3 -I -s -B - "$P" "$E" <<'PYCODE'
import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
v=dict(passed=True,inputs_sha256=hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest(),export_sha256=hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest())
(e/'10.json').write_text(json.dumps(v,sort_keys=True)+'\n')
PYCODE
printf '%s\n' 0 > "$P/a/1.txt"
SHELLCODE
nohup bash "$P/a/0.sh" </dev/null >"$P/a/0.log" 2>&1 &
printf '%s
' "$!" > "$P/a/0.txt"
