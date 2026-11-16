
import json,struct,urllib.request,sys,bisect
E=json.loads(sys.stdin.readline())
def get(u,rng=None):
    r=urllib.request.Request(u,headers={"Range":rng} if rng else {})
    with urllib.request.urlopen(r,timeout=60) as f: return f.status,f.read()
out={}
for tag,e in E.items():
    z=e["u"]; base=z.rsplit("/",1)[0]
    st,tr=get(base+"/lowres_wide.traj")
    rows=[l.split() for l in tr.decode().splitlines() if l.strip()]
    ts=[float(r[0]) for r in rows]
    st2,tail=get(z,"bytes=-70000")
    i=tail.rfind(b"PK\x05\x06"); n,cs,co=struct.unpack("<HII",tail[i+10:i+20])
    st3,cd=get(z,"bytes=%d-%d"%(co,co+cs-1))
    names=[];p=0
    while p+46<=len(cd) and cd[p:p+4]==b"PK\x01\x02":
        nl,el,cl=struct.unpack("<HHH",cd[p+28:p+34]); names.append(cd[p+46:p+46+nl].decode()); p+=46+nl+el+cl
    stamps=sorted(float(x.rsplit("_",1)[1][:-4]) for x in names if x.endswith(".png"))
    need=e["need"]
    exact=sum(1 for k,t,f in need if k<len(ts) and abs(ts[k]-t)<1e-5)
    near=0
    for t in ts:
        j=bisect.bisect_left(stamps,t)
        if any(0<=jj<len(stamps) and abs(stamps[jj]-t)<=0.002 for jj in (j-1,j)): near+=1
    out[tag]=dict(status=[st,st2,st3],traj_rows=len(ts),traj_first=ts[0],traj_last=ts[-1],members=len(names),png=len(stamps),
        stamp_first=stamps[0],stamp_last=stamps[-1],need=len(need),need_exact_traj_row=exact,traj_rows_with_member_2ms=near,
        need_max_k=max(k for k,_,_ in need),tail_bytes=len(tail),cd_bytes=len(cd),traj_bytes=len(tr))
print(json.dumps(out))
