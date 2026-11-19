F=/scratch/jjyeung/orch_n30/fb_pack; sed -n '/^## MUST/,$p' $F/patchArev/REVIEW_VERDICT.md | head -70; echo ====RELCNT2; ls $F/relcnt2/out; head -c 2500 $F/relcnt2/out/REPORT.md 2>/dev/null
