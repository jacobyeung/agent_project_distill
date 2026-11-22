export TZ=UTC; date -u +%TZ
timeout 90 srun --overlap --jobid 174444 -N1 -n1 env A15_JOB=174444 bash /tmp/a15_rh_174444/rh/stop.sh
