cd /scratch/jjyeung/orch_n30/sb_own400 || exit 1
echo ==== KIT_REPORT_B.md; cat out/KIT_REPORT_B.md
echo ==== core.py; cat kit/core.py
echo ==== inputs; ls -la kit/inputs
echo ==== score_400b; cat kit/score_400b.py
echo ==== worker; cat kit/worker.py
echo ==== MISSING_B; cat out/MISSING_B.json
echo ==== METHOD; cat out/METHOD_SOURCES_B.json
