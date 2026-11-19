R=/scratch/jjyeung/orch_n30; T=$R/sb_scale2/sb_scale_reports_1815Z.tgz
du -sh $R/sb_scale2/out/geometry $R/sb_scale2/out $R/sb_scale1/out | tr "\n" " "; echo
cd $R && tar czf $T --exclude='sb_scale2/out/geometry' sb_scale1/code sb_scale1/out sb_scale1/prompts sb_scale2/code sb_scale2/out sb_scale2/prompts sb_scalerev/REVIEW.md sb_scalerev/work/RECOMPUTE.json sb_scalerev/work/MRA_CHECK.json sb_scalerev/PROMPT.md
ls -l $T | awk '{print $5}'; sha256sum $T | cut -c1-64
timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "cat > /scratch/jjyeung/n30_mirror/swarm_build/sb_scale_reports_1815Z.tgz && sha256sum /scratch/jjyeung/n30_mirror/swarm_build/sb_scale_reports_1815Z.tgz | cut -c1-64" < $T
