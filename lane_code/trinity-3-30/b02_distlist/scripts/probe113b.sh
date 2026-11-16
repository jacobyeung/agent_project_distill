cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
echo "== obj"; ls -la obj | head -40
for t in $(ls obj | grep -E '^(masks|geometry)_.*\.tar$'); do echo "== TAR $t"; tar tvf obj/$t | awk '{print $3, $6}'; done
echo "== mask manifest"; ls -la obj/*/ 2>/dev/null | head -20
