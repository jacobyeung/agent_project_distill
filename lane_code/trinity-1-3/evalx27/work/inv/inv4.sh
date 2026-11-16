set +e
export TZ=UTC
O=/home/jjyeung/okit; R=$O/evalx_results
echo "== HOME top"; ls -la /home/jjyeung
for d in e193c2a3c e3da9a577 ebe307cf4; do echo "== $d EXIT"; cat $R/$d/EXIT.json; echo; echo "-- JOB.log"; cat $R/$d/JOB.log; echo; done
echo "== tar e193c2a3c"; tar tzvf $R/e193c2a3c/result.tar.gz | head -60; tar tzf $R/e193c2a3c/result.tar.gz | wc -l
echo "== q8 search"; ls -d /home/jjyeung/*/q8 /home/jjyeung/q8 /project/community/jjyeung/*/q8 2>/dev/null
