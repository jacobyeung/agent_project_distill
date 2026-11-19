#!/bin/bash
# place A and B (from S/BUILD.json), pull the four export parts once into A's a/e (no retries), fill A then B, dry checks; one nohup run
set -euo pipefail
umask 077
K=/project/community/jjyeung/okh7; S=/project/community/jjyeung/okh7/813f42db/r8test
read PA DA HA PB DB HB < <(/usr/bin/python3 -c "import json;b=json.load(open('$S/BUILD.json'));print(b['A']['package'],b['A']['delivery_dir'],b['A']['delivery_sha256'],b['B']['package'],b['B']['delivery_dir'],b['B']['delivery_sha256'])")
for X in A B; do
  if [ $X = A ]; then p=$PA; d=$DA; h=$HA; else p=$PB; d=$DB; h=$HB; fi
  printf '%s  %s\n' $h "$d/1.tgz" | sha256sum -c -
  test ! -e "$p"; mkdir -m 700 "$p"; tar -xzf "$d/1.tgz" -C "$p"; chmod 700 "$p/a"
done
cat > "$S/fill.sh" <<SHELLCODE
#!/bin/bash
set -euo pipefail
umask 077
export TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
S=$S; PA=$PA; PB=$PB; E=\$PA/a/e
OBJECT=q8/8865619b/6ed2c7aa_m400.tar; DONE=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done
test -f "\$DONE"; test ! -e "\$E"; mkdir -m 700 "\$E"
cp "\$DONE" "\$E/5"; cp /x/c.json "\$E/7"; cp /x/r.json "\$E/8"; cp /x/d.json "\$E/9"
f=(\$(cat "\$E/5")); test "\${f[0]}" = "\$OBJECT" && test "\${f[1]}" = 21583032321 && test "\${f[2]}" = 5555555555555555555555555555555555555555555555555555555555555555
for n in 7:2222222222222222222222222222222222222222222222222222222222222222 8:4444444444444444444444444444444444444444444444444444444444444444 9:3333333333333333333333333333333333333333333333333333333333333333; do test "\$(sha256sum "\$E/\${n%%:*}" | cut -d' ' -f1)" = "\${n#*:}"; done
for i in 0 1 2 3; do
  test ! -e "\$E/\$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/\$OBJECT.part0\$i-of-04" "\$E/\$i.partial"
  mv "\$E/\$i.partial" "\$E/\$i"; echo "\$(date -u +%TZ) part \$i"
done
for X in A B; do
  if [ \$X = A ]; then P=\$PA; T=05:00:00; D2=d2.py; else P=\$PB; T=02:30:00; D2=d2b.py; fi
  /usr/bin/python3 -I -s -B "\$P/a/4.py" --parts "\$E/0" "\$E/1" "\$E/2" "\$E/3" --done "\$E/5" --object "\$OBJECT" --config "\$E/7" --receipt "\$E/8" --data-receipt "\$E/9" --lineage SFT --step 400 --out "\$P/a/export.json" --prep-tar "\$P/a/6" --base-inputs "\$P/a/0.json" --inputs-out "\$P/a/1.json"
  PREP=\$(sha256sum "\$P/a/6" | cut -d' ' -f1)
  if ! /usr/bin/python3 -I -s -B \$S/d.py "\$P/a/1.json" "\$P/a/0.json" "\$PREP" > "\$S/dry_\$X.out" 2>&1; then echo "\$X DRY FAILED"; exit 1; fi
  (cd "\$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time \$T)
  if ! /usr/bin/python3 -I -s -B \$S/\$D2 "\$P" \$S/w2\$X > "\$S/dry2_\$X.out" 2>&1; then echo "\$X DRY2 FAILED"; exit 1; fi
  printf '%s\n' 0 > "\$P/a/1.txt"; echo "\$(date -u +%TZ) \$X filled, dry pass"
done
SHELLCODE
nohup bash "$S/fill.sh" </dev/null >"$S/fill.log" 2>&1 &
printf '%s\n' "$!" > "$S/fill.pid"; echo fill started pid $(cat $S/fill.pid) A=$PA B=$PB
