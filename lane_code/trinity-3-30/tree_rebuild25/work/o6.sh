export TZ=UTC; sacct -j 173964 -n -P -o JobID,JobName%20,State,ExitCode,Start,End,MaxRSS,MaxDiskWrite | awk -F'|' '$3!="COMPLETED" || NR<4' | head -20; sacct -j 173964 -n -o JobID | wc -l
sacct -j 173964 -n -P -o JobID,State,ExitCode,Elapsed,End --starttime 2026-11-21T01:40 | tail -8
