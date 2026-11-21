W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w26fix/n_go; A=$W/w24z11b/a_zffhb1q8/armed/kits/n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
diff -rq $A $F < /dev/null; diff <(sort -k2 $A/SHA256SUMS.txt) <(sort -k2 $F/SHA256SUMS.txt) < /dev/null
(cd $T && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$F'))" < /dev/null 2>&1 | tail -1)
cd /tmp; $P -I -c "
import json,base64,hashlib
for p in ('$A/BUILD.json','$F/BUILD.json'):
    b=json.load(open(p)); r=base64.b64decode(b['payload']); d=json.loads(r)
    print(p.split('/')[-3], {k:v for k,v in b.items() if k!='payload'}, 'payload_sha',hashlib.sha256(r).hexdigest()[:16]); print('  ',{k:(v if len(json.dumps(v))<120 else '...') for k,v in d.items()})
a=json.loads(base64.b64decode(json.load(open('$A/BUILD.json'))['payload'])); f=json.loads(base64.b64decode(json.load(open('$F/BUILD.json'))['payload']))
print('changed keys',[k for k in set(a)|set(f) if a.get(k)!=f.get(k)])
" < /dev/null
echo "== setrlimit in tree and kit"; grep -rn "setrlimit\|RLIMIT_AS" $T/student_pilot $T/launch_r1 --include=*.py < /dev/null | cut -c1-200; grep -n "setrlimit\|RLIMIT" $F/b/*.py $F/b/*.sh $F/job.sh < /dev/null | cut -c1-200
echo "== where production_proof imports admit"; grep -n "import admit\|s1_admission" $T/launch_r1/production_proof.py < /dev/null
echo "== grep a.py hash pinned anywhere in kit k/"; grep -l "e3ef430d0a09a21f" $F/k/* $F/BUILD.json < /dev/null 2>/dev/null; cd $F/k && for f in *.json; do $P -I -c "
import json,base64,sys
v=json.load(open('$F/k/'+sys.argv[1]))
r=base64.b64decode(v['payload']) if isinstance(v,dict) and 'payload' in v else json.dumps(v).encode()
print(sys.argv[1]) if b'e3ef430d0a09a21f' in r else None" $f < /dev/null; done
sed -n 50,75p $F/b/a.py < /dev/null
