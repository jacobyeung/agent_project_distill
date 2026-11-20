exec 3>&1 1>&2
cd /scratch/jjyeung/orch_n30/cont_ops24_c || exit 1
T=gbuild_cam_k3_20261120T1200Z.tar
F="gbuild/REPORT8.md gbuild/REPORT9.md gbuild/BRIEF_R8.md gbuild/BRIEF_R9.md gbuild/BRIEF_K2.md gbuild/BRIEF_K3.md gbuild/BRIEF_K3B.md gbuild/BRIEF_K3C.md gbuild/BRIEF_K3D.md gbuild/BRIEF_REV1.md gbuild/orchard_tower2x gbuild/orchard_tower2x_c cap/score_cam cap/score_bind/BINDING_R9.md cap/score_bind/BINDING_R9.json gbuild/orchard_tower2x_b/REPORT_K3.md gbuild/orchard_tower2x_b/SHA256SUMS_K3c $(ls gbuild/*round8* gbuild/*round9* 2>/dev/null | tr '\n' ' ')"
du -cb $F 2>/dev/null | tail -1
tar cf - --exclude='cpu-*' --exclude='admission-*' $F | tee >(sha256sum > /tmp/c25_m2.sha) | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "cat > /scratch/jjyeung/n30_mirror/cont_ops25/$T && sha256sum /scratch/jjyeung/n30_mirror/cont_ops25/$T && ls -la /scratch/jjyeung/n30_mirror/cont_ops25/$T"
sleep 1; echo SRC $(cat /tmp/c25_m2.sha)
cat gbuild/orchard_tower2x_c/returned/scored/TOWER2X_B.md >&3
