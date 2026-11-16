date -u +%FT%TZ; readlink -f /scratch/jjyeung/orch_cd
R=$(readlink -f /scratch/jjyeung/orch_cd)
for d in mdg_build mdg_build/work mdg_build/work/data evalx evalx/work ttower tower_read sam3_tower mdg_next; do echo "### $d"; ls -la $R/$d 2>&1 | head -40; done
echo "### shm du"; du -s /dev/shm/jjyeung_evalx/*/ 2>/dev/null | sort -rn | head -25
echo "### devs1c"; ls -la /dev/shm/jjyeung_evalx/devs1c_models /dev/shm/jjyeung_evalx/devs1c_models/* 2>&1 | head -30
