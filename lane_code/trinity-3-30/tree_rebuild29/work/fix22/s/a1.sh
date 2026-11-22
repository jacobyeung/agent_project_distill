W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W || exit 1
date -u +%TZ; df -h /scratch | tail -1
ls; echo ---work; ls work | tr '\n' ' '; echo
for d in d173881 d173864 d173912 d173817 d173677; do echo "== $d"; ls -la work/$d 2>&1 | head -30; done
echo ---w24y2; ls w24y2 w24y2/out 2>&1 | head; ls -d w24y2/*/rcj w24y2/*/*/rcj 2>/dev/null
echo ---w24z8b; ls w24z8b w24z8b/out 2>&1 | head -30
echo ---w24z11b; ls w24z11b w24z11b/out 2>&1 | head -30
echo ---w34; ls w34 2>&1 | head; ls w35 2>&1 | head
