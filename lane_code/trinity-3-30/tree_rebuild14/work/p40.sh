W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; date -u +%TZ
wc -c $W/w24/out/N_CARD_KIT_ROWS.md; cat $W/w24/out/N_CARD_KIT_ROWS.md
echo "== PINS"; nice -n 10 python3 -B /tmp/tr14_dec.py $K/k/c.json store_hashes,row_plan_sha256,room_authority,removal,exclusion,handover_receipt,init_artifact,depth_init,card,registry </dev/null | cut -c1-400 | head -40
ls -d /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev24* </dev/null
