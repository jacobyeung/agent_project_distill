export TZ=UTC; date -u +%TZ
timeout 120 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
D=/tmp/a15_f16_174198; R=$D/w1; T=$R/w/top; Q=/tmp/q_22c714e1_174198
echo "== $(date -u +%TZ) load $(cut -d' ' -f1-3 /proc/loadavg) df $(df -h /tmp | tail -1 | awk '{print $3"/"$2" free "$4}')"
cat $R/log/go.log | grep -v '  /' | cut -c1-160 | tail -n 4; echo "rc: $(cat $R/log/rc 2>/dev/null)"
echo "== q.err tail"; tail -c 700 $R/log/q.err 2>/dev/null
echo "== q.log lines $(wc -l < $R/log/q.log 2>/dev/null) tail"; tail -n 6 $R/log/q.log 2>/dev/null | cut -c1-330
echo "== A15 lines"; grep -h 'A15_' $R/log/q.log $R/log/q.err 2>/dev/null | cut -c1-400
echo "== tb"; tail -c 1500 $T/tb.txt 2>/dev/null
echo "== top"; ls -la --time-style=+%H:%M:%S $T/p 2>/dev/null | cut -c1-110; ls -la --time-style=+%H:%M:%S $T/p/q 2>/dev/null | cut -c1-110 | head -40; ls -la --time-style=+%H:%M:%S $T/p/q/selection 2>/dev/null | cut -c1-110
ps -u $(id -u) -o pid=,etime=,pcpu=,rss=,args= --width 150 | grep -v ' ps \|grep\|sleep\|srun\|slurmstepd' | grep 'a15_f16\|ta.py\|sc.py\|bwrap' | cut -c1-170 | head -8
/usr/bin/python3 -B -I - <<'PY'
import json,hashlib,os,sqlite3
Q='/tmp/q_22c714e1_174198'; T='/tmp/a15_f16_174198/w1/w/top'; NJ='/tmp/jjyeung/q_22c714e1'; NS='/tmp/q_22c714e1'
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
def enc(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def dg(v): return hashlib.sha256(enc(v).encode()).hexdigest()
EXP='522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39'
try:
    cfg=json.load(open(Q+'/n.json')); pin=cfg['s1_routing']['selection']; p=Q+pin['path'][len(NJ):]
    raw=open(p).read()
    print('== 174198 pool selection pin',pin['path'][-70:],pin['sha256'][:12],'file sha',sh(p)[:12],'prefix occurrences',raw.count(NJ),'sha256 with the prefix replaced',hashlib.sha256(raw.replace(NJ,NS).encode()).hexdigest())
except Exception as e: print('pool selection check failed',type(e).__name__,e)
w=T+'/p/q/n.json'
if os.path.exists(w):
    c=json.load(open(w)); print('== walk planned config n.json sha',sh(w)[:12],'s1_routing.selection',c['s1_routing']['selection'],'job strings NJ',open(w).read().count(NJ),'NS',open(w).read().count(NS+'/'))
r=T+'/p/q/selection/receipt.json'
if os.path.exists(r):
    v=json.load(open(r)); print('== walk selection receipt.json sha256',sh(r),'digest',dg(v),'== reviewed 522a3be3:',dg(v)==EXP)
    print('   database',v['database'],'source',v['source']['sha256'][:12],'count',v['count'])
    d=T+'/p/q/selection/rows.sqlite'; print('   rows.sqlite sha256',sh(d),'== N_DB 5e35c3ce:',sh(d).startswith('5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'))
res=T+'/p/q/RESULT.json'
if os.path.exists(res):
    v=json.load(open(res)); print('== walk RESULT status',v.get('status'),'steps',v.get('steps'),'refusal',str(v.get('refusal'))[:300])
PY
EOS
date -u +%TZ
