R=/scratch/jjyeung/orch_n30; cd $R; du -sh sb_own400/kit sb_own400/out | tr "\n" " "; echo
T=$R/sb_own400/sb_own400_kit_1835Z.tgz
tar czf $T --exclude='*.npz' --exclude='sb_own400/out/gpu' --exclude='sb_own400/out/execution_sources' --exclude='sb_own400/out/kit_before_b' sb_own400/kit sb_own400/prompts sb_own400/STATUS.md sb_own400/out/KIT_REPORT.md sb_own400/out/KIT_REPORT_B.md sb_own400/out/KIT_REPORT.json sb_own400/out/BARS_FROZEN.json sb_own400/out/BARS_FROZEN_B.json sb_own400/out/TEST_RESULTS.json sb_own400/out/TEST_RESULTS_B.json sb_own400/out/VALIDATION.json sb_own400/out/STAGE_228_B.json sb_own400/out/ENV_BOUNDARY_CHECK_B.json 2>&1 | tail -2
ls -l $T | awk '{print $5}'; sha256sum $T | cut -c1-64; sha256sum sb_own400/out/BARS_FROZEN.json | cut -c1-16
grep -o "multiplier[^.]*\.[0-9]*" sb_own400/out/KIT_REPORT_B.md | head -3
timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "cat > /scratch/jjyeung/n30_mirror/swarm_build/sb_own400_kit_1835Z.tgz && sha256sum /scratch/jjyeung/n30_mirror/swarm_build/sb_own400_kit_1835Z.tgz | cut -c1-64" < $T
awk -F'|' '{n++; s+=$6} END{print n" jobs "s" s wall"}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
