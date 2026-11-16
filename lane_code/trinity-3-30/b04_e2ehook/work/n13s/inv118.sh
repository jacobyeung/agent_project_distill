hostname -s; ls /scratch/jjyeung/orch_cd/ 2>&1 | head -40; echo ==; ls /scratch/jjyeung/orch_cd/devs1_direct /scratch/jjyeung/orch_cd/devs1_direct/* 2>&1 | head -40; echo ==k1; ls /scratch/jjyeung/k1 | head -30
for d in /scratch/jjyeung/k1/*/; do ls $d 2>/dev/null | grep -i -m3 "g3t\|safetensors\|weights" | sed "s|^|$d |"; done
ls -d /scratch/jjyeung/*frames* /scratch/jjyeung/orch_cd/*frames* 2>&1 | head
