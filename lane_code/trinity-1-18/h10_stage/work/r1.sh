K=/scratch/jjyeung/orch_n30/h1_headsft/kit/orchard_h10
cd $K && du -sh . && ls -la && find . -maxdepth 3 | head -200
echo ====OPS; cat OPERATIONS.md; echo ====OPEN; cat OPEN_INPUTS.md; echo ====STAGING; cat STAGING.md
