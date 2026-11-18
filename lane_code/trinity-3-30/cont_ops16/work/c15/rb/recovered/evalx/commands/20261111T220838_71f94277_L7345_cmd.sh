<!-- recovered by seal_plan: transcript=71f94277 line=7345 utc=2026-11-11T22:08:38.363Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; f=$(ls -t evalx/out/devin_traces/*.acp.jsonl | head -1); ls -la --time-style=+%H:%M:%S $f | cut -c30-140; python3 - "$f" <<'EOF'
import sys,json
lines=open(sys.argv[1]).read().splitlines()[-400:]
out=[]
for l in lines:
    try: d=json.loads(l)
    except Exception: continue
    m=d.get('message',{}); u=m.get('params',{}).get('update',{}) if isinstance(m,dict) else {}
    k=u.get('sessionUpdate')
    if k in('agent_message_chunk','agent_thought_chunk'):
        t=u.get('content',{}).get('text','')
        if t: out.append((d.get('at','')[11:19],k[6:9],t))
    elif k=='tool_call':
        out.append((d.get('at','')[11:19],'tool',str(u.get('title',''))[:120]))
s=''; last=None
res=[]
for at,k,t in out:
    if k in('mes','tho'):
        if last==k: res[-1]=(res[-1][0],k,res[-1][2]+t)
        else: res.append((at,k,t))
    else: res.append((at,k,t))
    last=k
for at,k,t in res[-14:]:
    print(at,k,t.replace('\n',' ')[:300])
EOF