export TZ=UTC; date -u +%TZ
timeout 120 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cut -c1-1500 /tmp/a15_f9_174134/f9.out | sed -n "/prepare dirs/,\$p" | tail -60; ls /tmp/q_22c714e1_174134/p/q/p/prepare_fc57fd0edeee4074bc80573f20b7dda7/prepared | head; sha256sum /tmp/q_22c714e1_174134/p/q/p/prepare_fc57fd0edeee4074bc80573f20b7dda7/prepared/pose_mix_order.json'
