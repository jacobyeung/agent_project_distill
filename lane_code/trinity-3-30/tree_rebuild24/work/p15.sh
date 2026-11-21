W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; O=$W/work/e3t_900003; ls -la $O 2>&1 | head; pgrep -af trinity.py | head -3
M='s#https?://[^ "]*#[URL]#g'; for f in $(ls $O/E3.json $O/*/E3.json $O/logs/* 2>/dev/null | head -12); do echo "== $f"; sed -E "$M" $f | tail -c 1500; done
