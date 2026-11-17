export TZ=UTC
P=/project/community/jjyeung; W=$P/okh7/e6fc152498; H=$P/cache/hf/hub
cat $W/l.done 2>/dev/null; ls -la $W
echo "== g3t blob"; readlink -f $H/models--thatbrguy--g3t/blobs/d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702; stat -L -c '%s %n' $H/models--thatbrguy--g3t/blobs/* ; sha256sum $H/models--thatbrguy--g3t/blobs/fab524bc2cd42f73ff370730aefabd1216398ee7
echo "== hub"; ls $H | head -60
cat > $W/h.sh <<'EOS'
cd /project/community/jjyeung/okh7/e6fc152498
while [ "$(wc -l < l.done 2>/dev/null || echo 0)" -lt 3 ]; do sleep 30; done
sha256sum /project/community/jjyeung/okh7/i_bb09a77d/m.tar > m.sha 2>&1; echo "m rc=$? $(date -u +%T)" >> h.done
sha256sum -b "$(readlink -f /project/community/jjyeung/cache/hf/hub/models--thatbrguy--g3t/blobs/d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702)" > g.sha 2>&1; echo "g rc=$? $(date -u +%T)" >> h.done
EOS
nohup nice -n 19 ionice -c3 bash $W/h.sh > /dev/null 2>&1 < /dev/null & echo hstarted $!
