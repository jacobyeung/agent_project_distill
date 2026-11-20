F=/scratch/jjyeung/orch_n30/fb_pack/donor3; ls $F/out | tr '\n' ' '; echo; grep -o '"[^"]*scale_donor[^"]*": *"[0-9a-f]*"' $F/out/*.json 2>/dev/null | head -5; grep "^+++ .*scale_donor" $F/out/PATCH_DONOR3.patch
ls -d $F/work/* 2>/dev/null | head; for t in $F/work/tree* $F/code; do [ -f $t/student_pilot/scale_donor.py ] && sha256sum $t/student_pilot/scale_donor.py; done 2>/dev/null | head
