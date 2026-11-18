R=/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz
ls -la $R; sha256sum $R; tar tzf $R | grep -E "budget_2048/request.json|^SPEC.json|^PLAN.json|merged/main" | head
