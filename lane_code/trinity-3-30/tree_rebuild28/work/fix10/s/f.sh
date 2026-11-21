export TZ=UTC
timeout 90 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_f10_174134 && ls -la cen lk && tar czf - cen/a.json cen/o.json cen/3.json lk/a.json ev_census.jsonl ev_plant.jsonl ev_prepare.jsonl run.out | base64 -w0'
