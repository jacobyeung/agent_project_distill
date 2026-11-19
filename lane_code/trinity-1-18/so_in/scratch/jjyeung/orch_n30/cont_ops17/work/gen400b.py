"""(gen400b: build_r10 = build_r8 + build_r9 wrap_batch) Write the Orchard scripts for the step-400 routed packages from one binding file posted by r1_ops (cont_ops17).
binding JSON keys: run, step, member_directory, object, lineage, config_sha256, base_identity, frame_layout,
preparation_sha256{config,receipt,data_receipt}, archive_bytes, archive_sha256, done (receipt path on Orchard),
prep_paths{config,receipt,data_receipt} (Orchard paths). Usage: gen400.py BINDING.json OUTDIR STAGE_HEX
Then: (1) o_build10.sh builds A/B (prints tokens); (2) edit nothing: o_place_pull_fill10.sh reads tokens from the build's BUILD.json."""
import json, sys
from pathlib import Path
b = json.loads(Path(sys.argv[1]).read_text()); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True); st = sys.argv[3]
K = '/project/community/jjyeung/okh7'; S = '%s/813f42db/%s' % (K, st)
assert b['run'] == '6ed2c7aa' and b['step'] in (400, 600) and b['member_directory'] == 'm%d' % b['step']
assert b['object'] == 'q8/8865619b/%s_m%d.tar' % (b['run'], b['step'])
keys = ('base_identity', 'config_sha256', 'frame_layout', 'lineage', 'member_directory', 'object', 'preparation_sha256', 'run', 'step', 'archive_bytes', 'archive_sha256')
bind = {k: b[k] for k in keys}
w = Path(__file__).resolve().parent
build = ('set -euo pipefail; umask 077; S=%s; test ! -e $S; mkdir -m 700 $S\n' % S
         + "cat > $S/b.py <<'PYEOF'\n" + (w/'build_r10.py').read_text().replace(
             "K = Path(os.environ.get('KROOT', '/project/community/jjyeung/okh7'))", "K = Path('/project/community/jjyeung/okh7')") + 'PYEOF\n'
         + "cat > $S/bind.json <<'JEOF'\n" + json.dumps(bind, sort_keys=True) + '\nJEOF\n'
         + "cat > $S/d.py <<'PYEOF'\n" + (w/'dryres2.py').read_text() + 'PYEOF\n'
         + "cat > $S/d2.py <<'PYEOF'\n" + (w/'dry2.py').read_text() + 'PYEOF\n'
         + "cat > $S/d2b.py <<'PYEOF'\n" + (w/'dry2b.py').read_text() + 'PYEOF\n'
         + '/usr/bin/python3 -I -s -B $S/b.py $S A,B $S/bind.json > $S/build.out 2>&1\n'
         + '/usr/bin/python3 -c "import json;b=json.load(open(\'$S/BUILD.json\'));[print(k,v[\'token\'],v[\'delivery_dir\'],v[\'delivery_sha256\']) for k,v in b.items()]"\n')
(out/'o_build10.sh').write_text(build)
pf = r'''#!/bin/bash
# place A and B (from S/BUILD.json), pull the four export parts once into A's a/e (no retries), fill A then B, dry checks; one nohup run
set -euo pipefail
umask 077
K=/project/community/jjyeung/okh7; S=@S@
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
OBJECT=@OBJECT@; DONE=@DONE@
test -f "\$DONE"; test ! -e "\$E"; mkdir -m 700 "\$E"
cp "\$DONE" "\$E/5"; cp @PCONFIG@ "\$E/7"; cp @PRECEIPT@ "\$E/8"; cp @PDATA@ "\$E/9"
f=(\$(cat "\$E/5")); test "\${f[0]}" = "\$OBJECT" && test "\${f[1]}" = @BYTES@ && test "\${f[2]}" = @SHA@
for n in 7:@SCONFIG@ 8:@SRECEIPT@ 9:@SDATA@; do test "\$(sha256sum "\$E/\${n%%:*}" | cut -d' ' -f1)" = "\${n#*:}"; done
for i in 0 1 2 3; do
  test ! -e "\$E/\$i"
  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/\$OBJECT.part0\$i-of-04" "\$E/\$i.partial"
  mv "\$E/\$i.partial" "\$E/\$i"; echo "\$(date -u +%TZ) part \$i"
done
for X in A B; do
  if [ \$X = A ]; then P=\$PA; T=05:00:00; D2=d2.py; else P=\$PB; T=02:30:00; D2=d2b.py; fi
  /usr/bin/python3 -I -s -B "\$P/a/4.py" --parts "\$E/0" "\$E/1" "\$E/2" "\$E/3" --done "\$E/5" --object "\$OBJECT" --config "\$E/7" --receipt "\$E/8" --data-receipt "\$E/9" --lineage @LINEAGE@ --step @STEP@ --out "\$P/a/export.json" --prep-tar "\$P/a/6" --base-inputs "\$P/a/0.json" --inputs-out "\$P/a/1.json"
  PREP=\$(sha256sum "\$P/a/6" | cut -d' ' -f1)
  if ! /usr/bin/python3 -I -s -B \$S/d.py "\$P/a/1.json" "\$P/a/0.json" "\$PREP" > "\$S/dry_\$X.out" 2>&1; then echo "\$X DRY FAILED"; exit 1; fi
  (cd "\$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time \$T)
  if ! /usr/bin/python3 -I -s -B \$S/\$D2 "\$P" \$S/w2\$X > "\$S/dry2_\$X.out" 2>&1; then echo "\$X DRY2 FAILED"; exit 1; fi
  printf '%s\n' 0 > "\$P/a/1.txt"; echo "\$(date -u +%TZ) \$X filled, dry pass"
done
SHELLCODE
nohup bash "$S/fill.sh" </dev/null >"$S/fill.log" 2>&1 &
printf '%s\n' "$!" > "$S/fill.pid"; echo fill started pid $(cat $S/fill.pid) A=$PA B=$PB
'''
rep = {'@S@': S, '@OBJECT@': b['object'], '@DONE@': b['done'], '@PCONFIG@': b['prep_paths']['config'],
       '@PRECEIPT@': b['prep_paths']['receipt'], '@PDATA@': b['prep_paths']['data_receipt'], '@BYTES@': str(b['archive_bytes']),
       '@SHA@': b['archive_sha256'], '@SCONFIG@': b['preparation_sha256']['config'], '@SRECEIPT@': b['preparation_sha256']['receipt'],
       '@SDATA@': b['preparation_sha256']['data_receipt'], '@LINEAGE@': b['lineage'], '@STEP@': str(b['step'])}
for k, v in rep.items(): pf = pf.replace(k, v)
(out/'o_place_pull_fill10.sh').write_text(pf)
print('wrote', out/'o_build10.sh', out/'o_place_pull_fill10.sh')
