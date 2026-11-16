export TZ=UTC
date -u +%H:%MZ
squeue -j 170035,170037 -o "%.10i %.24j %.8T %.20S %R" 2>&1
sacct -j 170035,170037 -X -o JobID,State,ExitCode,Start,End,Elapsed -P 2>&1
