cd /scratch/jjyeung/orch_n30/sb_cachk; wc -l kit_v2/mc_price.py kit_v2/mc_summary.py kit_v2/mc_score_guard.py kit_v2/run_cpu.sh
grep -n "argv\|def main\|seeds\|incomplete\|209\|missing\|raise\|BUDGET\|KILLED\|stopped" kit_v2/mc_price.py | head -60
echo ---; grep -n "argv\|def main\|final\|incomplete\|missing\|raise\|S_GT\|S_A0\|decision" kit_v2/mc_summary.py | head -60
echo ---; grep -n "def check\|raise\|exists\|capture_scores" kit_v2/mc_score_guard.py | head -30
echo ---; cat kit_v2/run_cpu.sh; sed -n 1,60p out/v2/KIT_REPORT.md
for f in BARS_AMENDMENT.json BARS_FROZEN.json FRAME_SETS.json GUARD.json KIT_MANIFEST.sha256 POPULATION.json STAGING.json; do sha256sum out/v2/$f; done
timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cd /scratch/jjyeung/orch_n30/sb_cachk/out/v2 && sha256sum BARS_AMENDMENT.json BARS_FROZEN.json FRAME_SETS.json GUARD.json KIT_MANIFEST.sha256 POPULATION.json STAGING.json && du -sh seeds && cat track/BUDGET.json | head -c 600; echo; ls track/S_A0_D64 | wc -l; ls track/S_GT_D64 | wc -l; ls track/S_A0_D64 | head -3'
