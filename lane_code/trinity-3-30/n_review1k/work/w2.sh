export TZ=UTC; date -u +%TZ
timeout 240 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
R=/tmp/a15_f16_174198/w1; T=$R/w/top; P=$T/p/q
echo "== go.log"; tail -n 4 $R/log/go.log | cut -c1-200; echo "rc: $(cat $R/log/rc 2>/dev/null)"
echo "== q.err tail"; tail -c 600 $R/log/q.err
echo "== q.log $(wc -l < $R/log/q.log) lines; keys of each JSON line (first 120 chars of non-row lines)"
grep -v '"rows_withheld"' $R/log/q.log | cut -c1-160 | head -60
echo "== admitted_census line"; grep -h '"admitted_census"' $R/log/q.log | head -1 | cut -c1-3000
echo "== phases"; ls -la --time-style=+%H:%M:%S $P/p $P/p/*/ 2>/dev/null | cut -c1-130 | head -50
/usr/bin/python3 -B -I - <<'PY'
import json, hashlib, glob, os
P='/tmp/a15_f16_174198/w1/w/top/p/q'
def sh(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
for d in sorted(glob.glob(P+'/p/prepare_*/routing/**/rows.sqlite', recursive=True)): print('prepared routing db', d[-60:], sh(d))
for r in sorted(glob.glob(P+'/p/prepare_*/**/receipt.json', recursive=True))[:8]:
    raw=open(r,'rb').read(); print('receipt', r[len(P):], 'bytes', len(raw), 'NJ', raw.count(b'/tmp/jjyeung/q_22c714e1'), 'NS/', raw.count(b'/tmp/q_22c714e1/'))
for j in sorted(glob.glob(P+'/p/*.json'))+sorted(glob.glob(P+'/p/*/*.json'))[:20]:
    try:
        v=json.load(open(j)); keys=list(v)[:12] if isinstance(v,dict) else type(v).__name__
        print('json', j[len(P):], keys, {k:v.get(k) for k in ('status','phase','complete','refusal') if isinstance(v,dict) and k in v})
    except Exception as e: print('json', j, e)
for q in glob.glob(P+'/p/frames_*/**/*.sqlite', recursive=True)+glob.glob(P+'/p/attempt_*/**/*.sqlite', recursive=True):
    print('sqlite', q[len(P):], os.path.getsize(q))
PY
ps -u $(id -u) -o pid=,etime=,pcpu=,rss=,args= --width 130 | grep 'ta.py\|wd.sh' | grep -v grep | cut -c1-150 | head -4
EOS
date -u +%TZ
