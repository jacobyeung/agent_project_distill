export TZ=UTC; date -u +%FT%TZ
scontrol show config 2>/dev/null | grep -iE 'JobContainerType|PrologFlags|TmpFS|Epilog|Prolog '
for f in /etc/slurm/job_container.conf /etc/slurm/slurm/job_container.conf; do [ -f $f ] && { echo "== $f"; grep -v '^#' $f | head -20; }; done
squeue -u jjyeung -h -o '%i|%j|%P|%T|%M|%l|%R' | grep -v jjy_
sacct -u jjyeung -X -n -P -S 2026-11-18T09:00 -o JobID,JobName,Partition,State,ExitCode,Start,End,NodeList | grep -v 'jjy_'
grep -n -iE 'tmp/jjyeung|cleanup' /project/community/jjyeung/okh7/x_7f1589c1.f172180/o/172180.proof.log | head -20
