W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; Z=$W/w24z8b/out; S=$W/work/s24m4z8b; test -e $S && { echo EXISTS; exit 1; }; mkdir -p $S
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; Z=W+'/w24z8b/out'; S=W+'/work/s24m4z8b'
d=json.load(open(Z+'/UPLOADS_24M4Z8B.json')); names=[l.strip() for l in open(Z+'/UPLOADS_24M4Z8B.list') if l.strip()]
e={x['name']:x for x in d['files']}; assert sorted(names)==sorted(e), (len(names),len(e))
sums=[];tot=0
for n in names:
    x=e[n]; assert not n.startswith('/') and '..' not in n.split('/')
    h=hashlib.sha256(open(x['local_path'],'rb').read()).hexdigest(); assert h==x['sha256'],n
    dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True); shutil.copyfile(x['local_path'],dst); os.chmod(dst,int(x.get('mode','0644'),8))
    sums.append('%s  %s'%(h,n)); tot+=x['bytes']
open(S+'/MANIFEST.sha','w').write('\n'.join(sums)+'\n'); print('files',len(names),'bytes',tot)
PY
cd $S && tar cf $W/work/s24m4z8b.tar . && sha256sum $W/work/s24m4z8b.tar && ls -l $W/work/s24m4z8b.tar
P=$Z/tree_rebuild_b24m4z8b_d891c672.tar; cut -c1-16 $P.sha256; sha256sum $P | cut -c1-16; timeout 200 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
echo ==PP; cat $Z/pp/pp.sh; echo ==JD7; head -30 $Z/../out/jd7.sh
