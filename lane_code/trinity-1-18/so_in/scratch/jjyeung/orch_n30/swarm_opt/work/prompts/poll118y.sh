#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
for c in so_cr_modep:cr_modep.md so_cr_pack_a:cr_pack_a.md; do n=${c%%:*}; [[ -d /scratch/jjyeung/orch_n30/$n ]] || bash $P/cursor_start.sh $n $P/${c##*:}; done
bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
G=/scratch/jjyeung/orch_n30/so_git/out/REPORT.md; head -c 1200 $G; echo; grep -n -i "real-git\|real git\|coordinator\|run_real_git" $G | cut -c1-300 | head -12
echo "=== modep"; head -c 3000 /scratch/jjyeung/orch_n30/so_modep/out/REPORT.md
