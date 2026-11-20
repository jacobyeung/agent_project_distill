C=/scratch/jjyeung/orch_n30/fb_pack/combo; cd $C/X && /scratch/jjyeung/envs/p1cpu/bin/python -B $C/seal.py $C/X | tail -1
cd $C && tar cf - out | timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "mkdir -p /scratch/jjyeung/n30_mirror/fb_pack/combo && cd /scratch/jjyeung/n30_mirror/fb_pack/combo && tar xf - && sha256sum out/*"
