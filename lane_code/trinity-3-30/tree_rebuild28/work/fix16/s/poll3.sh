export TZ=UTC; date -u +%TZ
timeout 150 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
D=/tmp/a15_f16_174198; R=$D/w1; T=$R/w/top; Q=/tmp/q_22c714e1_174198; P=$T/p/q
echo "== $(date -u +%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) df $(df -h /tmp | tail -1 | awk '{print $3"/"$2" free "$4}')"
tail -n 2 $R/log/go.log | cut -c1-160; echo "rc: $(cat $R/log/rc 2>/dev/null)"
echo "== q.err tail"; tail -c 900 $R/log/q.err 2>/dev/null
echo "== q.log lines $(wc -l < $R/log/q.log 2>/dev/null); last 3 (cut)"; tail -n 3 $R/log/q.log 2>/dev/null | cut -c1-260
echo "== A15 / timing lines"; grep -h 'A15_\|seconds=\|"ok"' $R/log/q.log $R/log/q.err 2>/dev/null | cut -c1-400
echo "== tb"; tail -c 1800 $T/tb.txt 2>/dev/null
echo "== p"; ls -la --time-style=+%H:%M:%S $T/p 2>/dev/null | cut -c1-100
echo "== p/q"; ls -la --time-style=+%H:%M:%S $P 2>/dev/null | cut -c1-100 | head -40
echo "== p/q/selection"; ls -la --time-style=+%H:%M:%S $P/selection 2>/dev/null | cut -c1-100
echo "== p/q/twins"; ls -la --time-style=+%H:%M:%S $P/twins 2>/dev/null | cut -c1-100 | head
echo "== p/q/p (admission)"; ls -la --time-style=+%H:%M:%S $P/p 2>/dev/null | cut -c1-120 | head -20
for d in $P/p/prepare_* $P/p/frames_*; do [ -d "$d" ] && { echo "== $d"; ls -la --time-style=+%H:%M:%S $d | cut -c1-120 | head -24; }; done
for d in $P/p/prepare_*/prepared $P/p/prepare_*/routing; do [ -d "$d" ] && { echo "== $d"; ls -la --time-style=+%H:%M:%S $d | cut -c1-120 | head -16; }; done
ps -u $(id -u) -o pid=,etime=,pcpu=,rss=,args= --width 130 | grep 'ta.py\|sc.py' | grep -v grep | cut -c1-150 | head -6
/usr/bin/python3 -B -I - <<'PY'
import json,hashlib,os,glob
T='/tmp/a15_f16_174198/w1/w/top'; P=T+'/p/q'; NJ='/tmp/jjyeung/q_22c714e1'; NS='/tmp/q_22c714e1'
N_DB='5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'; EXP='522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39'
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
def dg(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def count(p):
    raw=open(p,'rb').read(); return raw.count(NJ.encode()), raw.count((NS+'/').encode())
w=P+'/n.json'
if os.path.exists(w):
    c=json.load(open(w)); print('== planned config n.json sha',sh(w)[:12],'s1_routing.selection sha',c['s1_routing']['selection']['sha256'],'== reviewed source 74640a29:',c['s1_routing']['selection']['sha256'].startswith('74640a29'),'strings NJ/NS',count(w))
r=P+'/selection/receipt.json'
if os.path.exists(r):
    v=json.load(open(r)); print('== SELECTION receipt.json sha256',sh(r),'(reviewed regenerated_receipt 38c52f00...) digest',dg(v),'== reviewed 522a3be3:',dg(v)==EXP,'strings NJ/NS',count(r))
    d=P+'/selection/rows.sqlite'; h=sh(d); print('   rows.sqlite sha256',h,'== N_DB 5e35c3ce:',h==N_DB,'count',v['count'],'materialization',v['materialization']['sha256'][:12],'(6faab9cc)')
for name in ('twins/room_audit.json','v.json','m.json','c.json','RESULT.json','host.json'):
    p=P+'/'+name
    if os.path.exists(p): print('==',name,'bytes',os.path.getsize(p),'sha',sh(p)[:12],'strings NJ/NS',count(p))
for p in sorted(glob.glob(P+'/p/*.json'))+sorted(glob.glob(P+'/p/prepare_*/routing/receipt.json'))+sorted(glob.glob(P+'/p/prepare_*/prepared/*.json'))+sorted(glob.glob(P+'/p/frames_*/*.json')):
    print('==',p[len(P)+1:],'bytes',os.path.getsize(p),'sha',sh(p)[:12],'strings NJ/NS',count(p))
for p in sorted(glob.glob(P+'/p/prepare_*/routing/rows.sqlite')):
    h=sh(p); print('== PREPARED routing rows.sqlite',h,'== N_DB:',h==N_DB)
p=P+'/p/request.json'
if os.path.exists(p):
    v=json.load(open(p)); print('== admission request frame_roots',v.get('frame_roots'),'frame_root_map',v.get('frame_root_map'))
for p in sorted(glob.glob(P+'/p/frames_*/frame_inventory.sqlite*')): print('== frame audit file',p[len(P)+1:],'bytes',os.path.getsize(p))
res=P+'/RESULT.json'
if os.path.exists(res):
    v=json.load(open(res)); print('== RESULT status',v.get('status'),'steps',v.get('steps'),'refusal',str(v.get('refusal'))[:300])
PY
EOS
date -u +%TZ
