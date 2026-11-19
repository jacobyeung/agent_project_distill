R=/scratch/jjyeung/orch_n30
echo =====STAGE; cat $R/sb_ktrev2/out/STAGE_TOTALS.json | head -c 2500; echo
echo =====PHRASE; head -60 $R/sb_mask_phrase/out/PHRASE_REPORT.md; cat $R/sb_mask_phrase/out/*.sha256 2>/dev/null
echo =====MDREV2; cat $R/sb_mdrev2/REVIEW_VERDICT.md 2>/dev/null || cat $R/sb_mdrev2/out/REVIEW_VERDICT.md
echo =====CACHE; cat $R/sb_cachefix/out/CACHEFIX_REPORT.md; cat $R/sb_cachefix/out/*.sha256 2>/dev/null
echo =====CARRY; cat $R/sb_mask_carry/NOTICE_TWO_SESSIONS.md 2>/dev/null | head -15; ls $R/sb_mask_carry/out $R/sb_mask_carry/out/v2 2>/dev/null | tr "\n" " "; echo; head -60 $R/sb_mask_carry/out/v2/KIT_REPORT.md 2>/dev/null || head -60 $R/sb_mask_carry/out/KIT_REPORT.md
