export TZ=UTC; date -u +%TZ
timeout 90 srun --overlap --jobid 174198 -N1 -n1 bash /tmp/a15_rh_174198/rh/stop.sh
