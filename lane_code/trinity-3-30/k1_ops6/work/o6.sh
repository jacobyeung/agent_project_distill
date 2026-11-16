export TZ=UTC
date -u +%FT%TZ
sacct -j 170209 --format=JobID%20,JobName%30,Partition,State,ExitCode,Start,End,Elapsed,NodeList -P 2>&1 | head
echo "--- my jobs on general"; squeue -u $USER -p general -o '%.10i %.9P %.30j %.2t %.10M %.10l %.20S %R' 2>&1
