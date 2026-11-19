R=/scratch/jjyeung/orch_n30; cd $R
cat sb_ktfix2/out/FIX2_REPORT.md; cat sb_ktfix2/out/sb_ktfix2.tar.sha256; ls -la sb_ktfix2/out/sb_ktfix2.tar
echo =====; cat sb_ph2gate/out/PH2GATE_REPORT.md; cat sb_ph2gate/out/*.sha256; ls -la sb_ph2gate/out/*.tar
tail -2 $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
