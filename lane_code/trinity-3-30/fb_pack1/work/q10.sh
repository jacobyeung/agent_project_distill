R=/scratch/jjyeung/orch_n30; W=$R/tree_rebuild10_w
du -sh $W/w24/work/build24d $W/w24/work/build24f $W/ext $R/sb_fhalias $R/sb_auditfix2 /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7 $R/sb_rowD7f/out $W/w22/out $R/sb_own400/kit $R/fb_pack/route $R/fb_pack/prior $R/fb_pack/in 2>&1
du -sh --exclude='*.tar' $W/w24/out; ls $W/w24/work/build24d | head -30
