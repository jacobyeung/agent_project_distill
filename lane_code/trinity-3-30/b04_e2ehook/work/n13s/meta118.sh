set -u
F=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar
ls -la $F && sha256sum $F
cd $(dirname $F) && tar cf - e10fbb95.tar | timeout 300 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib 'mkdir -p /scratch/jjyeung/orch_n30/b04_e2ehook/work/meta && tar xf - -C /scratch/jjyeung/orch_n30/b04_e2ehook/work/meta && sha256sum /scratch/jjyeung/orch_n30/b04_e2ehook/work/meta/e10fbb95.tar'
cat /scratch/jjyeung/k1/g3t/SHA256SUMS /scratch/jjyeung/k1/g3t/config.json
ls /scratch/jjyeung/devs1_frames/00 | head -3; cat /scratch/jjyeung/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json | head -c 600
