cd /scratch/jjyeung/orch_n30 || exit 1
T=c25_final_20261120T1230Z.tar
F="cont_ops24_c/cap/score_conf cont_ops24_c/gbuild/REPORT10.md cont_ops24_c/gbuild/BRIEF_R10.md cont_ops24_c/cap/score_tower2x_b cont_ops25_c/arkit_lowres/out cont_ops25_c/arkit_lowres/STREAM.sha cont_ops25_c/SELECTION.json cont_ops25_c/r6_run.sh cont_ops25_c/r7_run.sh cont_ops25_c/r8_run.sh cont_ops25_c/r9_run.sh cont_ops25_c/r10_run.sh cont_ops25_c/k2_run.sh cont_ops25_c/k3_run.sh cont_ops25_c/k3b_run.sh cont_ops25_c/k3c_run.sh cont_ops25_c/k3d_run.sh cont_ops25_c/rev1_run.sh $(cd /scratch/jjyeung/orch_n30 && ls cont_ops24_c/gbuild/*round10* 2>/dev/null | tr '\n' ' ')"
du -cb $F 2>/dev/null | tail -1
tar cf - $F 2>/dev/null | tee >(sha256sum > /tmp/c25_m3.sha) | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cat > /scratch/jjyeung/n30_mirror/cont_ops25/$T && sha256sum /scratch/jjyeung/n30_mirror/cont_ops25/$T && ls -la /scratch/jjyeung/n30_mirror/cont_ops25/"
sleep 1; echo SRC $(cat /tmp/c25_m3.sha)
sha256sum cont_ops24_c/cap/t1.gz cont_ops24_c/cap/t2.gz cont_ops24_c/cap/dense.gz
df -h /scratch | tail -1
