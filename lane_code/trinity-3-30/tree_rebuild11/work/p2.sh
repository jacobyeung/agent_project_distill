W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr10|tr11"
tail -c 1200 $W/w19/work/build19/STATUS.md; ls -la $W/w19/out | tail -4
echo ---rows_a2; ls /scratch/jjyeung/n30_mirror/; ls -la /scratch/jjyeung/n30_mirror/rows_a2 | head -30; ls /scratch/jjyeung/n30_mirror/rows_a2/* -d 2>/dev/null | head; 
for d in /scratch/jjyeung/n30_mirror/rows_a2/*/; do echo "== $d"; ls $d | head -15; done 2>/dev/null | head -80
echo ---kitmeta; ls $W/w12/fixtures/work/kit07ca49df_meta/m/k/ | head -30
