cd /scratch/jjyeung
echo START $(date -u +%FT%TZ)
nice -n 19 tar cf - -T /scratch/jjyeung/orch_n30/lever1_m/PATHS.txt | tee >(sha256sum > /scratch/jjyeung/orch_n30/lever1_m/src_tar.sha) | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/n30_mirror/lever1 && cat > /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar && sha256sum /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar > /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar.sha256 && cat /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar.sha256'
echo "PIPE rc=${PIPESTATUS[*]}"; sleep 2; cat /scratch/jjyeung/orch_n30/lever1_m/src_tar.sha
echo DONE $(date -u +%FT%TZ)
