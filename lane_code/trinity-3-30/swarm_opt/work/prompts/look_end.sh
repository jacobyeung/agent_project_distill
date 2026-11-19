for t in so_step so_launch; do
 L=/scratch/jjyeung/orch_n30/$t; R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_$t | tail -1)
 echo "#### $t receipt $R"; ls $R; cat $R/receipt.json 2>/dev/null | head -30; echo "-- final"; tail -c 3000 $R/final_message.md 2>/dev/null; echo "-- dispatch"; tail -5 $L/work/dispatch.log; ls $L/out $L/out/patches
done
