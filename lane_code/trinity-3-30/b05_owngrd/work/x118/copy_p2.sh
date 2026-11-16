S=/dev/shm/jjyeung/b05; cd $S && sha256sum pilot2/resume.pt pilot2/train.jsonl pilot2/RUN.json
timeout 600 bash -c "tar cf - pilot2/resume.pt pilot2/train.jsonl pilot2/RUN.json pilot2_console.log code_p2 | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib 'cd /scratch/jjyeung/orch_n30/b05_owngrd_x118 && tar xf - && sha256sum pilot2/resume.pt'"
echo copy_rc=$?
tmux ls | grep b05; grep "AGG\|rc=\|Error" $S/diag/diag_p2_u200.log
