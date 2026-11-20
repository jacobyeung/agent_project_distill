W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24c/work/tree_r1; date -u +%TZ
cd $T && grep -rn -E "direct_schema_failure|schema_failure" --include=*.py . | grep -v "^./tests/" | head -20 | cut -c1-300
