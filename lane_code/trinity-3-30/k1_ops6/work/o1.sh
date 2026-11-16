export TZ=UTC
date -u +%FT%TZ
sacct -j 170206,170193 --format=JobID%20,JobName%30,Partition,State,ExitCode,Start,End,Elapsed,NodeList -P 2>&1 | head -20
echo "--- squeue general"
squeue -p general -o '%.10i %.9P %.30j %.8u %.2t %.10M %.10l %.20S %R' 2>&1 | head -20
echo "--- squeue me"
squeue -u $USER -o '%.10i %.9P %.30j %.2t %.10M %.10l %.20S %R' 2>&1 | head
P=/project/community/jjyeung/okh7/b7e31d84a90c62f5
echo "--- pool"
ls -la --time-style=+%FT%T $P/ 2>&1 | head -40
echo "--- 170206"
ls -laR --time-style=+%FT%T $P/170206 2>&1 | head -60
