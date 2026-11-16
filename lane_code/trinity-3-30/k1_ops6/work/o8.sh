export TZ=UTC
date -u +%FT%TZ
squeue -u $USER -t R -o '%.10i %.9P %.25j %.2t %.10M %.10l %b %C %m' 2>&1
sacct -j 170111 -X --format=JobID,Partition,AllocTRES%60,State -P 2>&1 | head -3
squeue -p general -u $USER -h | wc -l
