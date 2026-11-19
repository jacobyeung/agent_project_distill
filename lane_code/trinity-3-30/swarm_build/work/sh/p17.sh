R=/scratch/jjyeung/orch_n30
echo "@@FILE FIX4_REPORT.md"; cat $R/sb_ktfix2/out/FIX4_REPORT.md; cat $R/sb_ktfix2/out/sb_ktfix4.tar.sha256
echo "@@FILE FHALIAS2_REPORT.md"; cat $R/sb_fhalias/out/FHALIAS2_REPORT.md; cat $R/sb_fhalias/out/sb_fhalias2.tar.sha256
echo "@@FILE ALIAS2.patch"; cat $R/sb_fhalias/out/ALIAS.patch
echo "@@FILE FULL_INVENTORY2.md"; cat $R/sb_fullinv/out/FULL_INVENTORY.md; cat $R/sb_fullinv/out/sb_fullinv2.tar.sha256
echo "@@FILE PH2GATE3_REPORT.md"; cat $R/sb_ph2fix/out/PH2GATE3_REPORT.md
