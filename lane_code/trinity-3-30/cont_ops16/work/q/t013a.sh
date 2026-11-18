M=/scratch/jjyeung/n30_mirror
ls $M; ls -la $M/cont_ops $M/evalx27 2>&1 | head -30
for t in $M/evalx27/*.tar $M/cont_ops/readk_confirmed_1300Z.tar; do [ -f "$t" ] && { echo "-- $t"; tar tf $t | grep -E "e193/merged/main/results/budget_2048/request.json|arkit_3dod" | head -3; }; done
ls /scratch/jjyeung/orch_n30 2>/dev/null | head -40
