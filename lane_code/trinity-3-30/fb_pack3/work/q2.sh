F=/scratch/jjyeung/orch_n30/fb_pack; date -u +%TZ; df -h /scratch|tail -1
ls -la $F/mf/ 2>&1 | head; ls $F/cam/out | tr '\n' ' '; echo; ls $F/cam/out/intake 2>/dev/null | head; ls $F/cam/out/INTAKE* 2>/dev/null
grep -n "S2" $F/camrev/REVIEW_VERDICT.md | head -3 | cut -c1-300
ls /scratch/jjyeung/orch_n30/sb_own400/in/own_400 2>&1 | head; ls /scratch/jjyeung/orch_n30/sb_own400/out 2>&1 | head
