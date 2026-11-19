R=/scratch/jjyeung/orch_n30
echo "@@FILE ph2chk_REVIEW_VERDICT.md"; cat $R/sb_ph2chk/REVIEW_VERDICT.md
echo "@@FILE FULL_INVENTORY.md"; cat $R/sb_fullinv/out/FULL_INVENTORY.md; cat $R/sb_fullinv/out/*.sha256
echo "@@FILE FHALIAS_REPORT.md"; cat $R/sb_fhalias/out/FHALIAS_REPORT.md; cat $R/sb_fhalias/out/*.sha256; wc -c $R/sb_fhalias/out/ALIAS.patch
echo "@@FILE ALIAS.patch"; head -c 12000 $R/sb_fhalias/out/ALIAS.patch
