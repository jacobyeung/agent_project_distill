# Finish the boot-first change in r4kit (workspace cap raised)

Continue in `/scratch/jjyeung/orch_n30/lever1_c/r4kit/` under `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R4BOOT.md` and all earlier briefs (rules hold; FROZEN.json unchanged; local /scratch reads approved, do not stop to ask; no ssh/git/network/GPU/kill/Slurm; no /home or /data*).
Your previous session implemented the boot-first order and stopped because the workspace (20.11 GB) exceeded the 10 GB cap. The lane raises the cap to 35 GB for this package (trinity-2-28 /scratch has 2.9 TB free). Delete nothing; if a rebuildable intermediate must move, put it under `/scratch/jjyeung/orch_n30/lever1_c/r4kit/tmp/`.
Finish exactly what BRIEF_R4BOOT.md asks: the missing-module test (zero bulk bytes staged, cause back through the production fetch), all tests re-run, out/delivery.tgz rebuilt and validation passed for its exact sha256, PLACE.md/REPORT.md/BUILD.json/FORECAST.json agree (fix PLACE.md's stale test count too), the new order and pre-bulk bytes and seconds stated. Keep token f68a2d7c903be. Change nothing else.
Final message: the new order with file:line, tests, token, delivery sha256 and bytes, workspace size. Be quick.
