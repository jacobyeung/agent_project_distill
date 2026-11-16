export TZ=UTC; date -u +%FT%TZ
squeue -j 170379 -h -o '%i %T %M %N'; cat /project/community/jjyeung/okh7/db3954b2/logs/dserial.170379.log; ls /project/community/jjyeung/okh7/db3954b2/parts 2>&1
for f in /project/community/jjyeung/okh7/db3954b2/logs/*.170379t*_0.log; do echo "== $f"; grep -v '^{"t"' $f | tail -8; grep '^{"t"' $f | tail -1; done
grep -h -i '"err' /project/community/jjyeung/okh7/db3954b2/parts/a0n3/out.jsonl 2>/dev/null | head -3 | cut -c1-400
