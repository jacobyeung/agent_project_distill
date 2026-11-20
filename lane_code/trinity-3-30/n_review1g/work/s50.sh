W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Y=$W/w24y2; X=$W/w24x2; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1g; T=$N/r1f/tcpx
mkdir -p $R; date -u +%TZ; tmux ls 2>&1 | grep -i 'tr2\|pkg' ; df -h /scratch | tail -1
ls $Y $Y/out $Y/work 2>&1 | head -60
ls $Y/out/*.sha256 2>/dev/null && cat $Y/out/*.sha256
for f in $Y/work/build24m4y2/PACKAGE_CHECK.json $Y/out/PACKAGE_CHECK.json; do [ -f $f ] && { echo "== $f"; head -c 1500 $f; echo; }; done
tail -5 $Y/work/build24m4y2/package_rerun_lane.log 2>&1
for k in $(ls -d $Y/work/*/kits/* $Y/out/kit_* 2>/dev/null); do [ -f $k/SHA256SUMS.txt ] || continue; echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64)"; (cd $T && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 | tail -1); done
