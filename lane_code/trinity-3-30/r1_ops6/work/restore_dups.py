import gzip,os,shutil,sys
SRC='/scratch/jjyeung/distill_sync/repo/lane_code/trinity-1-3'
DST='/scratch/jjyeung/orch_n30/r1_ops6/rec'
pre=('r1_ops/','r1_pkt/','r1_ops2/','r1_ops3/','r1_ops4/','r1_ops5/')
n=miss=0
for line in gzip.open(SRC+'/code_sync/meta/DEDUP_trinity-1-3.tsv.gz','rt',errors='surrogateescape'):
    dup,kept=line.rstrip('\n').split('\t')
    if not dup.startswith(pre): continue
    s=SRC+'/'+kept; d=DST+'/'+dup
    if os.path.exists(d): continue
    if not os.path.exists(s): miss+=1; continue
    os.makedirs(os.path.dirname(d),exist_ok=True); shutil.copy2(s,d); n+=1
print('restored',n,'missing',miss)
