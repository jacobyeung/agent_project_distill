#!/bin/bash
# progress signature of the watcher's newest raw: live listing, node logs, job cgroup usage, progress count
M=/scratch/jjyeung/orch_n30/n_ops1/work/mon
now=$(grep -m1 '^@@NOW' $M/last.raw | cut -d' ' -f2)
st=$(grep -A1 '^@@SACCT' $M/last.raw | tail -1 | cut -d'|' -f4,6)
s=$(awk '/^@@LIVE/{f=1} /^@@NR/{f=0} f' $M/last.raw; grep -E '^@@LOG|^@@PCOUNT|^@@RCPT' $M/last.raw; grep '^@@CG' $M/last.raw | grep -v step_ | grep -oE 'cur=[0-9]+'; awk '/^@@ODIR/{f=1} /^@@NODE/{f=0} f' $M/last.raw)
echo "$now $st sig=$(echo "$s" | md5sum | cut -c1-8) logs: $(grep '^@@LOG' $M/last.raw | awk '{print $2"="$3}' | tr '\n' ' ') $(grep '^@@CG' $M/last.raw | grep -v step_ | grep -oE 'cur=[0-9]+|cpu_usec=[0-9]+' | tr '\n' ' ') j2=$(awk '/^@@ODIR/{f=1} /^@@NODE/{f=0} f' $M/last.raw | grep ' j2.log' | awk '{print $5}')"
