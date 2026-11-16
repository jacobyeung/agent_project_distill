set -u
X=/scratch/jjyeung/orch_n30/b05_owngrd/work/x118
date -u +%FT%TZ > $X/stage113.START
tar cf - -C /scratch/jjyeung/envs sam3_capretry_native_v1 -C /scratch/jjyeung/orch_cd/ttower/work/sam3_weights sam3.pt -C /scratch/jjyeung/orch_cd/mdg_next/work/data sam3src -C /scratch/jjyeung/k1_frames -T $X/frames286.txt | timeout 3600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "mkdir -p /dev/shm/jjyeung/b05/stage && cd /dev/shm/jjyeung/b05/stage && tar xf - && du -sh /dev/shm/jjyeung/b05 && sha256sum sam3.pt && ls | wc -l"
echo rc=$? >> $X/stage113.log
date -u +%FT%TZ > $X/stage113.END
