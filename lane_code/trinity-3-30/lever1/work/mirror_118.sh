set -u
cd /scratch/jjyeung
M=/scratch/jjyeung/orch_n30/lever1_m; mkdir -p $M
L=""
for p in orch_n30/e3_geom orch_n30/k1_ops3/work/e3gd orch_n30/k1_ops3/work/codex_arkit_timing orch_n30/k1_ops3/work/gt_sets orch_n30/k1_ops3/work/manifest_v2 orch_n30/k1_ops3/work/K1_MANIFEST.staged.json orch_n30/k1_ops3/work/kc_guard orch_n30/k1_ops3/kc/k1_build/work/kit_k1a orch_n30/gt_build/out/K1_GT_RASTERS_259.tar orch_n30/gt_build/out/RASTERS_SHA256SUMS orch_n30/gt_build/out/PIN_CHECK.tsv orch_n30/geo_k1 orch_n30/sb_kbox4 orch_n30/b04host3 orch_cd/leg_s1_tree orch_cd/evalx/work/milestone/native_package_s24_05 orch_cd/dose_pool n30_mirror/gt_audit n30_mirror/tower_redecide n30_mirror/sb_headacc2 orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4/src; do
  if [ -e "$p" ]; then L="$L $p"; else echo "MISSING $p"; fi
done
echo "$L" | tr ' ' '\n' | sed '/^$/d' > $M/PATHS.txt
du -s --block-size=1M $L | tee $M/SIZES.txt
cat > $M/run.sh <<RUN
cd /scratch/jjyeung
echo START \$(date -u +%FT%TZ)
nice -n 19 tar cf - -T $M/PATHS.txt | tee >(sha256sum > $M/src_tar.sha) | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/n30_mirror/lever1 && cat > /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar && sha256sum /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar > /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar.sha256 && cat /scratch/jjyeung/n30_mirror/lever1/k1x_inputs.tar.sha256'
echo "PIPE rc=\${PIPESTATUS[*]}"; sleep 2; cat $M/src_tar.sha
echo DONE \$(date -u +%FT%TZ)
RUN
tmux new-session -d -s l1_mirror "bash $M/run.sh > $M/run.log 2>&1"
sleep 3; tmux ls | grep l1_; cat $M/run.log
