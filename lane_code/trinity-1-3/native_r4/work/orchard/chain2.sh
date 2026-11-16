until grep -q "complete /project" /scratch/jjyeung/orch_n30/native_r4/dl/upb2.log; do if ! tmux has-session -t nr5_upb2 2>/dev/null && ! grep -q complete /scratch/jjyeung/orch_n30/native_r4/dl/upb2.log; then echo "push ended without complete" > /scratch/jjyeung/orch_n30/native_r4/work/orchard/chain2.out; exit 1; fi; sleep 20; done
cd /scratch/jjyeung/orch_n30/native_r4/work/orchard
timeout 2400 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < q7_packet2.sh > q7.out 2>&1; rc=$?; echo "q7 rc $rc" >> q7.out
[ $rc -eq 0 ] && grep -q "u.py ok" q7.out || { echo "q7 failed" > chain2.out; exit 1; }
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < q8_sbatch2.sh > q8.out 2>&1; echo "q8 rc $?" >> q8.out
echo done > chain2.out
