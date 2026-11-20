W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls | grep tr2
for z in w24z7 w24z8; do echo "== $z"; ls -lt $W/$z/out | head -8; ls $W/$z/out/*.tar.sha256 2>/dev/null; done
tail -c 600 $W/work/b24m4z8.log; ls $W/w24z7/out/tgcs $W/w24z7/out/e3
