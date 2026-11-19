R=/scratch/jjyeung/orch_n30; S=$R/sb_stage228; cd $S; date -u +%TZ
cat > pipe_union.sh <<'X'
cd / && date -u +%FT%TZ > /scratch/jjyeung/orch_n30/sb_stage228/union.start
nice -n 10 tar cf - --no-recursion -T /scratch/jjyeung/orch_n30/sb_stage228/union.list 2>/scratch/jjyeung/orch_n30/sb_stage228/union.tar.err | timeout 7200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'tar xf - -C /'
echo "rc=${PIPESTATUS[*]} $(date -u +%FT%TZ)" > /scratch/jjyeung/orch_n30/sb_stage228/union.done
X
cat > pipe_ph2.sh <<'X'
date -u +%FT%TZ > /scratch/jjyeung/orch_n30/sb_stage228/ph2.start
nice -n 10 cat /scratch/jjyeung/orch_n30/sb_ph2fix/out/sb_ph2fix2.tar | timeout 7200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib "bash -c 'mkdir -p /scratch/jjyeung/orch_n30/sb_ph2fix && tee >(sha256sum > /scratch/jjyeung/orch_n30/sb_ph2fix/RECV_TAR.sha256) | tar xf - -C /scratch/jjyeung/orch_n30/sb_ph2fix'"
echo "rc=${PIPESTATUS[*]} $(date -u +%FT%TZ)" > /scratch/jjyeung/orch_n30/sb_stage228/ph2.done
X
tmux new-session -d -s sb_stage228u "bash $S/pipe_union.sh"
tmux new-session -d -s sb_stage228p "bash $S/pipe_ph2.sh"
sleep 20; ls -la $S; tmux ls | grep stage228
