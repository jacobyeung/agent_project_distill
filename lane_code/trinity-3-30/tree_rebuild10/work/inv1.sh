hostname -s; date -u +%FT%TZ; free -g | head -2; df -BG --output=avail /scratch | tail -1; tmux ls 2>&1 | head -20
ls /scratch/jjyeung/envs 2>&1 | head; ls /scratch/jjyeung/envs/p1cpu/bin/python 2>&1
echo "== orch_n30"; ls /scratch/jjyeung/orch_n30 2>&1 | tr '\n' ' '; echo
echo "== orch_n30/tree_rebuild"; ls -la /scratch/jjyeung/orch_n30/tree_rebuild 2>&1 | head -40
echo "== n30_mirror"; ls /scratch/jjyeung/n30_mirror 2>&1 | tr '\n' ' '; echo
for d in tree_rebuild rows_r2 rows_r1 r1_pkt rows_rebuild count_diag r1_ops r1_ops4 r1_ops5 r1_ops6; do echo "== m/$d"; ls -la /scratch/jjyeung/n30_mirror/$d 2>&1 | head -25; done
du -sh /scratch/jjyeung/n30_mirror/* 2>/dev/null | head -40
