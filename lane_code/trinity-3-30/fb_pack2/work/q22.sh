F=/scratch/jjyeung/orch_n30/fb_pack; tail -c 300 $F/priorrev/cursor.log; echo; sed -n "1,/^## Verified/p" $F/priorrev/REVIEW_VERDICT.md | head -45
