set -u
cd /scratch/jjyeung/orch_n30/b04_e2ehook_m544h/m544
tar cf - heads.pt artifact.json full_weights/full_weights.json | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib 'set -u; D=/dev/shm/jjyeung/exports/m544_heads; mkdir -p $D && tar xf - -C $D && cd $D && sha256sum heads.pt artifact.json full_weights/full_weights.json; ls -d /scratch/jjyeung/devs1_frames /dev/shm/jjyeung_mdg_next/g3t 2>&1; du -sh /scratch/jjyeung/devs1_frames 2>&1 | tail -1; ls /scratch/jjyeung/devs1_frames | head -5; ls /scratch/jjyeung/devs1_frames | wc -l; ls /dev/shm | head -20'
echo PIPE_RC=$?
