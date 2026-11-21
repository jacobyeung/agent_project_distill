W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
hostname -s; date -u; df -h /scratch | tail -1; nproc; free -g | sed -n 2p
ls -la $W | head -80
echo ---w26fix2; ls -la $W/w26fix2 | head -60
echo ---n_go; ls -la $W/w26fix2/n_go | head -60
echo ---n_go/b; ls -la $W/w26fix2/n_go/b | head -80
echo ---w27fix; ls -la $W/w27fix 2>&1 | head
