date -u +%FT%TZ > /scratch/jjyeung/orch_n30/sb_stage228/ph2.start
nice -n 10 cat /scratch/jjyeung/orch_n30/sb_ph2fix/out/sb_ph2fix2.tar | timeout 7200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib "bash -c 'mkdir -p /scratch/jjyeung/orch_n30/sb_ph2fix && tee >(sha256sum > /scratch/jjyeung/orch_n30/sb_ph2fix/RECV_TAR.sha256) | tar xf - -C /scratch/jjyeung/orch_n30/sb_ph2fix'"
echo "rc=${PIPESTATUS[*]} $(date -u +%FT%TZ)" > /scratch/jjyeung/orch_n30/sb_stage228/ph2.done
