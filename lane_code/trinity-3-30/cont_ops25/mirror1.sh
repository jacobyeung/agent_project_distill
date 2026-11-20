cd /scratch/jjyeung/orch_n30/cont_ops24_c || exit 1
T=gbuild_t1_r67_20261120T0905Z.tar
F="cap/t1.gz cap/t1ret cap/score_t1 cap/score_t2/NPZ_SELF_CONSISTENCY_R6.json cap/score_t2/S2_ANALYSIS.json cap/score_t2/S2_ANALYSIS.md cap/score_t2/ROUND6.validation.json $(cd /scratch/jjyeung/orch_n30/cont_ops24_c && ls gbuild/REPORT6.md gbuild/REPORT7.md gbuild/SHA256SUMS7 gbuild/BRIEF_R6.md gbuild/BRIEF_R7.md gbuild/*round6* gbuild/*round7* 2>/dev/null | tr '\n' ' ')"
echo $F
du -cb $F | tail -1
tar cf - $F | tee >(sha256sum > /tmp/c25_m1.sha) | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "mkdir -p /scratch/jjyeung/n30_mirror/cont_ops25 && cat > /scratch/jjyeung/n30_mirror/cont_ops25/$T && sha256sum /scratch/jjyeung/n30_mirror/cont_ops25/$T && ls -la /scratch/jjyeung/n30_mirror/cont_ops25/"
sleep 1; echo SRC $(cat /tmp/c25_m1.sha)
