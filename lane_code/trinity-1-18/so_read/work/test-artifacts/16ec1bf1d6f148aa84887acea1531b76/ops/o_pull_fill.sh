#!/bin/bash
set -euo pipefail
umask 077
D=$(cd -- "$(dirname -- "$0")" && pwd)
P=/project/community/jjyeung/okh7/a15_cot_apab0123456789
if [ "${1:-}" != --worker ]; then
  mkdir -m 700 "$P/a/0.lock"
  test ! -e "$P/a/1.txt"
  nohup bash "$0" --worker </dev/null >"$P/a/0.log" 2>&1 &
  printf '%s\n' "$!" > "$P/a/0.txt"
  exit 0
fi
test -d "$P/a/0.lock"
fin(){ rc=$?; printf '%s\n' "$rc" > "$P/a/1.txt"; exit "$rc"; }
trap fin EXIT
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
E=$P/a/e
test ! -e "$E"
mkdir -m 700 "$E"
OBJECT=q8/8865619b/673bc60f_m600.tar
cp /project/community/jjyeung/okh7/abcdef/5 "$E/5"
/usr/bin/python3 -I -s -B -c 'import sys; from pathlib import Path; assert Path(sys.argv[1]).read_text().split() == sys.argv[2:]' "$E/5" q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222
cp /project/community/jjyeung/okh7/abcdef/7 "$E/7"
test "$(sha256sum "$E/7" | cut -d' ' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1
cp /project/community/jjyeung/okh7/abcdef/8 "$E/8"
test "$(sha256sum "$E/8" | cut -d' ' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915
cp /project/community/jjyeung/okh7/abcdef/9 "$E/9"
test "$(sha256sum "$E/9" | cut -d' ' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"
done
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"
