# n_ops1 batched Orchard check (read-only). Placeholders: __J__ (job id or 0), __MP__ (cached metrics path or -)
export TZ=UTC; J=__J__; MP='__MP__'; X=/project/community/jjyeung/okh7/x_22c714e1
echo "@@NOW $(date -u +%FT%TZ)"
echo "@@SQ"; squeue -u $USER -h -o "%i|%j|%P|%T|%M|%l|%L|%R|%N|%S"
echo "@@NEWEST $(ls $X/j/ 2>/dev/null | grep -E '^[0-9]+\.out$' | sort -n | tail -1)"
echo "@@DF $(df -BG --output=avail /project/community | tail -1 | tr -d ' G')"
if [[ $J != 0 ]]; then
 echo "@@SACCT"; sacct -j $J -X -n -P -o JobID,JobName%40,Partition,State,ExitCode,Elapsed,Timelimit,AllocTRES%90,NodeList,Submit,Start,End
 echo "@@SCTL"; scontrol show job $J 2>/dev/null | tr ' ' '\n' | grep -E '^(JobName|Command|WorkDir|StdOut|StdErr|TimeLimit|RunTime|NodeList|Partition|JobState|Reason)=' | cut -c1-300
 O=$X/j/$J.out
 echo "@@JOUT $(stat -c %s $O 2>/dev/null || echo -1)"
 test -f $O && grep -v "_cgroup_procs_check\|unable to read" $O | grep -E "gpu0|resolve|^[0-9a-f]{64}$|stage |frames f|init mirror|overlay on|^\{\"v\"|ADMIT|REFUS|Traceback|Error|error|E[0-9][0-9]|job done|rc=|Killed|CANCEL|DUE TO|oom" | cut -c1-300 | tail -40
 echo "@@JTAIL"; test -f $O && grep -v "_cgroup_procs_check\|unable to read" $O | tail -6 | cut -c1-300
 echo "@@ODIR"; ls -la --time-style=+%T $X/o/$J 2>/dev/null | tail -n +4
 test -f $X/o/$J/o.tar && { echo "@@OTAR"; cat $X/o/$J/RESULT.json 2>/dev/null; echo; for m in q.log rooms.log t.log; do tar xzOf $X/o/$J/o.tar $m 2>/dev/null | tail -4 | cut -c1-400; done; }
 if squeue -j $J -h -o %T 2>/dev/null | grep -q RUNNING; then
  echo "@@NODE"
  timeout 150 srun --overlap --jobid $J -n1 -N1 timeout 120 nice -n 19 bash -s <<'INNER' 2>&1 | cut -c1-600
J=__J__; MP='__MP__'
INNER_BODY
INNER
  echo "@@SRUN rc=${PIPESTATUS[0]}"
 fi
fi
echo "@@EXTRA"
EXTRA_BODY
echo "@@END"
