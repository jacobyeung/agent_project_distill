set +e
export TZ=UTC
O=/home/jjyeung/okit; K=/project/community/jjyeung/okh7
echo "== okh7 top"; ls -la $K
echo "== j depth3"; find $K/j -maxdepth 3 -printf '%y %10s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | sort -k4 | head -150
echo "== r depth3"; find $K/r -maxdepth 3 -printf '%y %10s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | sort -k4 | head -150
echo "== du j r"; du -sh $K/j $K/r 2>&1
echo "== evalx_results"; ls -la $O/evalx_results; du -sh $O/evalx_results
echo "== x p u i"; find $O/x $O/p $O/u $O/i -maxdepth 2 -printf '%y %10s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | head -80
echo "== aliases"; for a in 3e0e8a36 8b677689 f3069074.tar; do find $O $K /project/community/jjyeung -maxdepth 4 -name "$a*" -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p -> %l\n' 2>/dev/null; done
echo "== changed after 15:32Z"; find $O $K -newermt '2026-11-15 15:32:00' -maxdepth 6 -printf '%y %s %TY-%Tm-%TdT%TH:%TM:%TS %p\n' 2>/dev/null | head -60
