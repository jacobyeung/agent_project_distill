W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr10|tr11"
tail -c 600 $W/w19/work/build19/STATUS.md; tail -3 $W/work/build19_dispatch.log; ls -la $W/w19/out | tail -3
wc -c $W/w19/out/BUILD19_REPORT.md; cat $W/w19/out/BUILD19_REPORT.md
