export TZ=UTC
D=/project/community/jjyeung/okh7/x_f5c353f7
ls -la $D/runs/359fcc3c/ 2>&1 | head -30
ls $D/o | grep -E '^17011[01]' | tr '\n' ' '; echo
for f in $D/runs/359fcc3c/*.json $D/o/170111*.json $D/o/170109*.json; do test -f $f && echo "$f $(stat -c %s $f) v314=$(grep -o v314_execution_disagreement $f | wc -l) ord=$(grep -o object_rel_direction_hard $f | wc -l)"; done 2>/dev/null
R=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5e1d07a4/f/h/r16/receipt.json
ls -la $R 2>&1; test -f $R && { sha256sum $R; echo "v314=$(grep -o v314_execution_disagreement $R | wc -l)"; }
