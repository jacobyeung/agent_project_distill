export TZ=UTC; date -u +%TZ
timeout 120 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cut -c1-900 /tmp/a15_f9_174134/f9.out | sed -n "/prepare dirs/,/store pose_a2v3/p"; wc -c /tmp/a15_f9_174134/f9_result.json'
