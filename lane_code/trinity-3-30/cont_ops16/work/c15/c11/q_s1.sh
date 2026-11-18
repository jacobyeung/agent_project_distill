export TZ=UTC
timeout 60 srun --overlap --jobid 170710 -n1 bash -c 'cd /tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4/inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066 && tar cf - prepared/s1_receipt.json config.json | base64 -w0; echo' 2>&1; echo "srun_rc=$?"
