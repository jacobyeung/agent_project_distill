cd /scratch/jjyeung
for d in k1 k1_frames orch_cd orch_n30/k1_ops3 orch_n30/b04host3 orch_n30/cont_ops24_c/gbuild/cap orch_n30/cont_ops24_c/gt orch_n30/cont_ops25_c/cam/gt orch_n30/cont_ops25_c/cam/reads devs1_frames; do echo "## $d"; ls $d 2>/dev/null | head -25; timeout 60 du -s --block-size=1M $d 2>/dev/null; done
ls -la orch_n30/cont_ops24_c/gbuild/cap | head -40
ls orch_n30/cont_ops24_c/gt/* 2>/dev/null | head; find orch_n30/cont_ops24_c/gt -maxdepth 3 -type f | wc -l
