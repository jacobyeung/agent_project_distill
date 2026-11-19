V=/scratch/jjyeung/orch_n30/sb_cachk/out/v2; T=/scratch/jjyeung/orch_n30/sb_cachk/work/sb_carry_priced_1555Z.tgz
tar czf $T -C $V CARRY_REPORT.md CARRY_DECISION.json K1_CARRY.json PER_ITEM.jsonl price TIMING_RECEIPT.json BARS_FROZEN.json BARS_AMENDMENT.json POPULATION.json track/BUDGET.json track/EVENTS.jsonl -C /scratch/jjyeung/orch_n30/sb_cachk/work price_s5.sh price_s5.log
ls -l $T; sha256sum $T
timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "mkdir -p /scratch/jjyeung/n30_mirror/swarm_build && cat > /scratch/jjyeung/n30_mirror/swarm_build/sb_carry_priced_1555Z.tgz && sha256sum /scratch/jjyeung/n30_mirror/swarm_build/sb_carry_priced_1555Z.tgz" < $T
