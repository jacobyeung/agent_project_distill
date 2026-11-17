W=/project/community/jjyeung/okh7/e6fc152498; cd $W
cat > b.sh <<'EOS'
set -u
W=/project/community/jjyeung/okh7/e6fc152498; cd $W; mkdir -p -m 700 e g
export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1
B=gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar
i=0
for gen in 1794665056278014 1794665041985097 1794665039963627 1794665051797628; do
  gsutil -q cp "$B.part0$i-of-04#$gen" e/$i.partial > e/$i.log 2>&1; rc=$?
  [ $rc -eq 0 ] && mv e/$i.partial e/$i
  echo "pull $i rc=$rc $(date -u +%T)" >> b.done
  [ $rc -eq 0 ] || exit 1
  i=$((i+1))
done
(cd e && sha256sum 0 1 2 3 > ../e.sha); echo "esha rc=$? $(date -u +%T)" >> b.done
cat e/0 e/1 e/2 e/3 | sha256sum > e.whole.sha; echo "ewhole rc=$? $(date -u +%T)" >> b.done
H=/project/community/jjyeung/cache/hf/hub/models--thatbrguy--g3t/blobs
tar -chf g/0.partial --format=gnu --owner=0 --group=0 --numeric-owner --mtime=@0 --mode=0644 \
  --transform 's,^d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702$,g/model.safetensors,;s,^fab524bc2cd42f73ff370730aefabd1216398ee7$,g/config.json,' \
  -C $H d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702 fab524bc2cd42f73ff370730aefabd1216398ee7; rc=$?
[ $rc -eq 0 ] && mv g/0.partial g/0; echo "gtar rc=$rc $(date -u +%T)" >> b.done
tar tvf g/0 >> b.done; (cd g && sha256sum 0 > ../g0.sha; stat -c '%s' 0 >> ../g0.sha); echo "gsha rc=$? $(date -u +%T)" >> b.done
EOS
nohup nice -n 19 ionice -c3 bash b.sh > b.out 2>&1 < /dev/null & echo bstarted $!
