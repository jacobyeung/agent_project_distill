O=/project/community/jjyeung/okh7/x_ee227714/o
python3 - <<'P'
import json,statistics as st
F="/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/metrics_172660.jsonl"
D={}
for l in open(F):
    d=json.loads(l); D[d["step"]]=d["ranks"]
S=sorted(D); print("steps",S[0],S[-1],len(S))
G=lambda r,k:r[k]
def row(s):
    rk=D[s]; o=[s]
    for n in("pose","vqa","routing","pointing"):
        v=[r["stream_means"].get(n) for r in rk]; o.append("%s:%s"%(n,",".join("%.3g"%x if x is not None else "None" for x in v)))
    o.append("wall:%s"%",".join("%.1f"%r["wall_seconds"] for r in rk))
    o.append("data:%.1f"%rk[0]["data_seconds"])
    o.append("ck:%.0f"%rk[0].get("checkpoint_seconds",0))
    return " | ".join(map(str,o))
for s in [201,202,210]+list(range(380,421)):
    if s in D: print(row(s))
print("COMPONENTS")
for s in [201,202,210]+list(range(380,421,5)):
    if s in D:
        r=D[s][0]; print(s,{k:float("%.3g"%v) for k,v in r["components"].items()})
print("MEDIANS 300-400 (rank-mean)")
def rm(s,f): 
    v=[f(r) for r in D[s]]; v=[x for x in v if x is not None]; return sum(v)/len(v) if v else None
for n in("pose","vqa","routing","pointing"):
    v=[rm(s,lambda r:r["stream_means"].get(n)) for s in range(300,401) if s in D]; v=[x for x in v if x is not None]
    print(n,"median %.4g min %.3g max %.3g n=%d"%(st.median(v),min(v),max(v),len(v)))
for c in("pose","depth","vqa","pointing","routing"):
    v=[D[s][0]["components"][c] for s in range(300,401) if s in D]; print("comp",c,"median %.4g"%st.median(v))
v=[max(r["wall_seconds"] for r in D[s]) for s in range(300,401) if s in D]; print("wall median(max rank)",st.median(v))
v=[rm(s,lambda r:r["wall_seconds"]) for s in range(300,401) if s in D]; print("wall median(rank-mean)",st.median(v))
print("MEMORY GB (rank: after_opt alloc/res, peak alloc/res)")
for s in [201,202,210,300,400]:
    print(s," ; ".join("r%d %.1f/%.1f pk %.1f/%.1f"%(r["rank"],r["memory"]["after_optimizer_step"]["allocated_bytes"]/1e9,r["memory"]["after_optimizer_step"]["reserved_bytes"]/1e9,r["peak_allocated_bytes"]/1e9,r["peak_reserved_bytes"]/1e9) for r in D[s]))
P
echo ---steps; head -c 700 $O/172660.steps; echo; tail -n 3 $O/172660.steps | cut -c1-300
echo ---w.steps; head -c 500 $O/172660.w.steps
echo ---gpu; head -n 8 $O/172660.gpu | cut -c1-300
