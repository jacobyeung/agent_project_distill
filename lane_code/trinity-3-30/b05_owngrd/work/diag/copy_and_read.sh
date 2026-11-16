S=/dev/shm/jjyeung/b05
grep -v -i "warn\|pynvml" $S/diag/diag600.log | tail -60 | cut -c1-260
cd $S && sha256sum pilot/export/head.safetensors pilot/resume.pt pilot/train.jsonl pilot/RUN.json
timeout 600 bash -c "tar cf - pilot/export pilot/resume.pt pilot/train.jsonl pilot/RUN.json pilot_console.log | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib 'mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd_x118 && cd /scratch/jjyeung/orch_n30/b05_owngrd_x118 && tar xf - && sha256sum pilot/export/head.safetensors pilot/resume.pt && df -h /scratch | tail -1'"
echo copy_rc=$?
