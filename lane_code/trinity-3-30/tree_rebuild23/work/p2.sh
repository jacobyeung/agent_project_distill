W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w24y2; date -u +%TZ
tmux ls 2>&1 | grep -E "tr2"; ls -l $J/out/tree_rebuild_b24m4y2_* ; tail -3 $J/work/build24m4y2/package_rerun_lane.log
which bwrap unshare; bwrap --version 2>&1; cat /proc/sys/user/max_user_namespaces
M=$W/work/enospc_probe; mkdir -p $M/mnt
timeout 30 unshare -Urm sh -c "mount -t tmpfs -o size=1m tmpfs $M/mnt && dd if=/dev/zero of=$M/mnt/f bs=64k count=40 2>&1 | tail -1; df -h $M/mnt | tail -1" 2>&1 | tail -3
timeout 30 bwrap --dev-bind / / --size 1048576 --tmpfs $M/mnt sh -c "dd if=/dev/zero of=$M/mnt/f bs=64k count=40 2>&1 | tail -1" 2>&1 | tail -2
sed -n 1,60p $J/out/BUILD24M4Y2_REPORT.md 2>/dev/null | head -20
ls $J/kit_n 2>/dev/null | head; ls $J/out/kit_n_go | head
