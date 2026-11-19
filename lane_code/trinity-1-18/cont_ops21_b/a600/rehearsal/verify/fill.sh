#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
S=$S; PA=$PA; E=$PA/a/e
OBJECT=q8/8865619b/6ed2c7aa_m600.tar; DONE=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m600.done
test -f "$DONE"; test ! -e "$E"; mkdir -m 700 "$E"
cp "$DONE" "$E/5"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json "$E/7"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json "$E/8"; cp /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/data_receipt.json "$E/9"
f=($(cat "$E/5")); test "${f[0]}" = "$OBJECT" && test "${f[1]}" = 21583032320 && test "${f[2]}" = 673c147c46bd5a64a991e023307b6e2676f1c2cb96c564ca236ab7c914e2c430
for n in 7:b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad 8:a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda 9:03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47; do test "$(sha256sum "$E/${n%%:*}" | cut -d' ' -f1)" = "${n#*:}"; done
for i in 0 1 2 3; do
  test ! -e "$E/$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"
  mv "$E/$i.partial" "$E/$i"; echo "$(date -u +%TZ) part $i"
done
for X in A; do
  P=$PA; T=03:00:00; D2=d2.py
  /usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
  PREP=$(sha256sum "$P/a/6" | cut -d' ' -f1)
  if ! /usr/bin/python3 -I -s -B $S/d.py "$P/a/1.json" "$P/a/0.json" "$PREP" > "$S/dry_$X.out" 2>&1; then echo "$X DRY FAILED"; exit 1; fi
  (cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time $T)
  if ! /usr/bin/python3 -I -s -B $S/$D2 "$P" $S/w2$X > "$S/dry2_$X.out" 2>&1; then echo "$X DRY2 FAILED"; exit 1; fi
  printf '%s\n' 0 > "$P/a/1.txt"; echo "$(date -u +%TZ) $X filled, dry pass"
done