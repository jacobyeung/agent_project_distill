K=/project/community/jjyeung/okh7
for f in $K/x27ret/a8acc277397/result.tar.gz $K/ae71c903_fetched/adff67f7ae9/result.tar.gz $K/ae71c903_fetched/a5d2d909067/result.tar.gz $K/ae71c903_fetched/acb2faedd41/result.tar.gz; do echo "$(stat -c %s $f) $(sha256sum $f)"; done
tar tzf $K/x27ret/a8acc277397/result.tar.gz | grep -E "SPEC.json|PLAN.json|budget_2048/request.json" | head
