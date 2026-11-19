R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ
sed -n 30,95p sb_cachk/kit_v2/launch_gpu.sh | grep -n -E 'CUDA|card|CARD|index|select|idle' | head -15 | cut -c1-220
cat sb_stage228/union_stats.json | head -8
cat > sb_stage228/verify.py <<'X'
import os,json,sys
L=[l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
nf=nb=miss=0
for p in L:
    try: s=os.lstat(p)
    except FileNotFoundError: miss+=1; continue
    import stat
    if stat.S_ISREG(s.st_mode): nf+=1; nb+=s.st_size
print(json.dumps(dict(entries=len(L),present=len(L)-miss,missing=miss,files=nf,bytes=nb)))
X
python3 - <<'X'
import os,stat,json
L=[l.rstrip('\n') for l in open('/scratch/jjyeung/orch_n30/sb_stage228/union.list') if l.strip()]
nf=nb=0
for p in L:
    s=os.lstat(p)
    if stat.S_ISREG(s.st_mode): nf+=1; nb+=s.st_size
print('SRC',json.dumps(dict(entries=len(L),files=nf,bytes=nb)))
X
cat sb_stage228/union.list | timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/sb_stage228 && cat > /scratch/jjyeung/orch_n30/sb_stage228/union.list'
cat sb_stage228/verify.py | timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'cat > /scratch/jjyeung/orch_n30/sb_stage228/verify.py; cd /scratch/jjyeung/orch_n30/sb_stage228 && echo -n "DST "; nice -n 10 python3 verify.py union.list; cat /scratch/jjyeung/orch_n30/sb_ph2fix/RECV_TAR.sha256; ls /scratch/jjyeung/orch_n30/; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo; nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader'
