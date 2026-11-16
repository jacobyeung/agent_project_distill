<!-- recovered by seal_plan: transcript=71f94277 line=17851 utc=2026-11-13T07:42:20.959Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/leg_s1_tree; tail -c 300000 out/devin_traces/devin_20261113T020002Z_2886271.acp.jsonl | /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import sys, json
out=[]
for line in sys.stdin:
    try: d=json.loads(line)
    except Exception: continue
    u=d.get("message",{}).get("params",{}).get("update",{})
    k=u.get("sessionUpdate")
    if k=="tool_call":
        raw=u.get("rawInput") or {}
        t=u.get("title") or ""
        cmd=raw.get("command") or raw.get("cmd") or raw.get("path") or ""
        out.append(d.get("at","")[11:19]+" CALL "+(str(t)+" | "+str(cmd))[:260].replace("\n"," "))
    elif k=="agent_message_chunk":
        c=u.get("content",{}).get("text","")
        if c.strip(): out.append(d.get("at","")[11:19]+" SAY "+c[:200].replace("\n"," "))
print("\n".join(out[-22:]))
'