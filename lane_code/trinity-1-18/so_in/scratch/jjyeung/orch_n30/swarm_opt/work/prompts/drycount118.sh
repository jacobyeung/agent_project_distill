T=/scratch/jjyeung/orch_n30/so_git/out/tools
cd /scratch/jjyeung/orch_n30 && tar cf - so_git/out/tools so_git/out/patches so_git/out/MANIFEST.json | base64 -w0; echo
for d in /scratch/jjyeung/orch_n30/so_* /scratch/jjyeung/orch_n30/sb_*; do [[ -d $d && ! -L $d ]] || continue; LCS_ENABLE_DRY_COUNT=1 nice -n 10 timeout 120 bash $T/dry_count.sh $d 2>&1 | tail -1; done > /scratch/jjyeung/orch_n30/so_git/work/drycount_118.txt
wc -l /scratch/jjyeung/orch_n30/so_git/work/drycount_118.txt; head -3 /scratch/jjyeung/orch_n30/so_git/work/drycount_118.txt
bash /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/qrun.sh
