#!/bin/bash
# runs on Orchard login node under nohup: pull four m100 parts sequentially, then fill pins
set -uo pipefail
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
P=/project/community/jjyeung/bf94a7976a7e9; D=/project/community/jjyeung/okh7/6b960af0
OBJECT=q8/8865619b/17c4ffa4_m100.tar; DONE=/project/community/jjyeung/okh7/x_3fdda0fb/o/gcs_17c4ffa4_m100.done
L=$P/a/pull.log; echo "start $(date -u +%TZ)" >> $L
test -f "$DONE" || { echo "no done" >> $L; exit 1; }
for i in 0 1 2 3; do
  test ! -e "$P/a/e/$i" || { echo "exists $i" >> $L; exit 1; }
  gsutil -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$P/a/e/$i.partial" >> $L 2>&1; rc=$?
  [ $rc -eq 0 ] && mv "$P/a/e/$i.partial" "$P/a/e/$i"
  echo "pull $i rc=$rc $(date -u +%TZ)" >> $L; [ $rc -eq 0 ] || exit 1
done
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$P/a/e/0" "$P/a/e/1" "$P/a/e/2" "$P/a/e/3" \
  --done "$DONE" --object "$OBJECT" --config "$D/i/c.json" --receipt "$D/i/r.json" --data-receipt "$D/i/d.json" \
  --lineage SFT --step 100 --out "$P/a/export.json" --prep-tar "$P/a/e/4" \
  --base-inputs /project/community/jjyeung/b01ec87a6f29b/a/1.json --inputs-out "$P/a/1.json" >> $L 2>&1
echo "fill rc=$? $(date -u +%TZ)" >> $L
cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:00:00 >> $L 2>&1
echo "check rc=$? $(date -u +%TZ)" >> $L
