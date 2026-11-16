R=/project/community/jjyeung/vla_libero
echo "HOST $(hostname) $(date -u)"
ls -la $R 2>&1
for d in $R/*/; do echo "== $d"; ls -la $d 2>&1 | head -60; done
echo "== KIT_SHA256"; find $R -maxdepth 4 -name 'KIT_SHA256*' 2>/dev/null | head; for f in $(find $R -maxdepth 4 -name 'KIT_SHA256*' 2>/dev/null | head -3); do echo "-- $f"; head -c 3000 $f; echo; done
echo "== du"; timeout 120 du -sh $R/* 2>&1 | head -40
echo "== kit tree"; find $R -maxdepth 3 -path '*kit*' 2>/dev/null | head -150
