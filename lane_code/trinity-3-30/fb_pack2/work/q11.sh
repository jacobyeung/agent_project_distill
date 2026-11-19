F=/scratch/jjyeung/orch_n30/fb_pack; kill -CONT 1803846 $(pgrep -P 1803846); ps -o pid,stat -p 1803846 | tail -1
echo ====CAMFORMREV; sed -n '1,/^## Verified/p' $F/camformrev/REVIEW_VERDICT.md | head -40
echo ====PRIOR2B; head -c 4500 $F/prior2b/out/REPORT.md
echo; echo ====DONOR2; head -c 4500 $F/donor2/out/REPORT.md
