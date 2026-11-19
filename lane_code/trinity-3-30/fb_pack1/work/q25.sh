F=/scratch/jjyeung/orch_n30/fb_pack; sed -n '/^## SHOULD/,$p' $F/camrev/REVIEW_VERDICT.md | head -40; grep -n -i "two forms\|mixed\|style\|hazard" $F/camrev/REVIEW_VERDICT.md | head
