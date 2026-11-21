W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
hostname -s; date -u +%TZ
ls $W | head -50
echo ---- w28fix; ls -la $W/w28fix | head -60
echo ---- find
find $W/w28fix $W/w27fix -maxdepth 6 -name carrier_c1_run.py 2>/dev/null | head -20
