D=/scratch/jjyeung/orch_n30/sb_maskfail
echo "=== LS lane"; ls -la $D 2>&1 | head -40
echo "=== LS out"; ls -la $D/out 2>&1 | head -60
for f in FIRST_TABLE.md RULES.md MASKFAIL_REPORT.md; do
  for p in $D/out/$f $D/$f; do
    if [ -f "$p" ]; then echo "=== FILE $p ($(stat -c %s "$p") bytes)"; head -c 60000 "$p"; echo; fi
  done
done
for p in $D/out/MASKFAIL.json $D/MASKFAIL.json; do
  if [ -f "$p" ]; then echo "=== JSON $p ($(stat -c %s "$p") bytes)"; head -c 6000 "$p"; echo; fi
done
echo "=== STATUS"; [ -f $D/STATUS.md ] && head -c 6000 $D/STATUS.md
