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
OBJECT=q8/8865619b/6ed2c7aa_m400.tar
cp /project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done "$E/5"
/usr/bin/python3 -I -s -B -c 'import sys; from pathlib import Path; assert Path(sys.argv[1]).read_text().split() == sys.argv[2:]' "$E/5" q8/8865619b/6ed2c7aa_m400.tar 21583032320 dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5
cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json "$E/7"
test "$(sha256sum "$E/7" | cut -d' ' -f1)" = b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad
cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json "$E/8"
test "$(sha256sum "$E/8" | cut -d' ' -f1)" = a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda
cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/data_receipt.json "$E/9"
test "$(sha256sum "$E/9" | cut -d' ' -f1)" = 03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"
done
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 400 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"
