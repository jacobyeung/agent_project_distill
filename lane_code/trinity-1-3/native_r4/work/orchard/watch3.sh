O=/scratch/jjyeung/orch_n30/native_r4/work/orchard
while true; do
  date -u +%FT%TZ >> $O/watch3.log
  timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < $O/q11_sbatch3.sh > $O/q11.last 2>&1; rc=$?
  cat $O/q11.last >> $O/watch3.log; echo "rc $rc" >> $O/watch3.log
  if grep -q "Submitted batch job" $O/q11.last; then cp $O/q11.last $O/q11.out; echo SUBMITTED >> $O/watch3.log; exit 0; fi
  if grep -q "FAIL past" $O/q11.last; then echo CUTOFF >> $O/watch3.log; exit 0; fi
  if ! grep -q "FAIL own job" $O/q11.last; then echo "UNEXPECTED" >> $O/watch3.log; exit 1; fi
  sleep 240
done
