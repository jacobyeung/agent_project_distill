ls /scratch/jjyeung/n30_mirror < /dev/null | tr '\n' ' '; echo; ls /scratch/jjyeung/orch_n30 < /dev/null | tr '\n' ' '; echo; df -h /scratch < /dev/null | tail -1
for d in /scratch/jjyeung/n30_mirror/*/; do ls $d < /dev/null | head -3 | sed "s|^|$d |"; done 2>/dev/null | head -80
