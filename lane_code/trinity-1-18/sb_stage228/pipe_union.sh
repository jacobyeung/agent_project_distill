cd / && date -u +%FT%TZ > /scratch/jjyeung/orch_n30/sb_stage228/union.start
nice -n 10 tar cf - --no-recursion -T /scratch/jjyeung/orch_n30/sb_stage228/union.list 2>/scratch/jjyeung/orch_n30/sb_stage228/union.tar.err | timeout 7200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'tar xf - -C /'
echo "rc=${PIPESTATUS[*]} $(date -u +%FT%TZ)" > /scratch/jjyeung/orch_n30/sb_stage228/union.done
