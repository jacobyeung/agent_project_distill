K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z7/out/kit_n_go
grep -n "launch_shell(" $K/b/*.py | cut -c1-300; for f in $(grep -l "launch_shell(" $K/b/*.py); do n=$(grep -n "launch_shell(" $f | tail -1 | cut -d: -f1); sed -n "$((n-12)),$((n+1))p" $f | cut -c1-260; done; ls $K; cat $K/job.sh | head -20 | cut -c1-200
