#!/usr/bin/env python3
import json, re, os, hashlib, collections, sys
W="/scratch/jjyeung/orch_n30/seal_plan/work"; OUT=sys.argv[1]
TARGET=["rs_tree","rs_rows","rs_contracts","rs_cover","dx_census","b11_native","b6_build","b6_design","k1_build","k1_ops","official544","evalx","leg_s1_review","next_queue","nq_review","trace_ruling","policy_audit","dense_plan","tree_review","tree_review2","tree_review3","o3_cache","scene_evidence","dose_pool","label_247","pool_r2","own_probe","grd_selector","devs1_masks","mask_recall","mdg_next","orchard_cp2","leg_s1_tree","legs1_routed","geo_bakeoff","vla_libero","vla_nav","vla_heads"]
LABRE=re.compile(r"(?<![A-Za-z0-9_])(rs_tree|rs_rows|rs_contracts|rs_cover|dx_census|b11_native|b6_build|b6_design|k1_build|k1_ops|official544|evalx|leg_s1_review|next_queue|nq_review|trace_ruling|policy_audit|dense_plan|tree_review[123]?|o3_cache|scene_evidence|dose_pool|label_247|pool_r2|own_probe|grd_selector|devs1_masks|mask_recall|mdg_next|orchard_cp2|leg_s1_tree|legs1_routed|geo_bakeoff|vla_libero|vla_nav|vla_heads)(?:\d+[a-z]?|_s\d+\w*)?(?![A-Za-z0-9])")
CRED=re.compile(r"(AIza[0-9A-Za-z_\-]{30,}|(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_\w{20,}|hf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|xox[bpa]-[A-Za-z0-9\-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|(?i:aws_secret_access_key)\s*[=:]\s*\S{20,}|Bearer [A-Za-z0-9_\-\.]{25,}|(?i:(api[_-]?key|password|passwd|secret|token))\s*[=:]\s*['\"]?[A-Za-z0-9_\-/+]{16,})")
ORCH="/scratch/jjyeung/orch_cd/"
index=[]; counts=collections.Counter(); excluded=[]
def lanes_in(s): return sorted(set(m.group(1) for m in LABRE.finditer(s)))
def save(lane, kind, ts, tx, line, orig, name, body, extra=""):
    if CRED.search(body):
        excluded.append((lane,kind,ts,tx,line,orig)); return
    ts_s=(ts or "nots").replace(":","").replace("-","").replace(".","")[:15]
    d=os.path.join(OUT,lane,kind); os.makedirs(d,exist_ok=True)
    fn=re.sub(r"[^A-Za-z0-9_.\-]","_",name)[-90:]
    p=os.path.join(d,f"{ts_s}_{tx}_L{line}_{fn}")
    i=1
    while os.path.exists(p): p=os.path.join(d,f"{ts_s}_{tx}_L{line}_{i}_{fn}"); i+=1
    hdr=f"<!-- recovered by seal_plan: transcript={tx} line={line} utc={ts} kind={kind} original_path={orig} {extra} -->\n"
    open(p,"w").write(hdr+body)
    b=(hdr+body).encode()
    index.append([lane,kind,ts or "",tx,str(line),orig,os.path.relpath(p,os.path.dirname(OUT)),str(len(b)),hashlib.sha256(b).hexdigest()[:16]])
    counts[(lane,kind)]+=1
def lane_of_path(p):
    rest=p[len(ORCH):]; comp=rest.split("/")[0]
    return comp if comp in TARGET else "_other/"+(comp if "/" in rest else "_root")
HD=re.compile(r"(?:cat|tee(?:\s+-a)?)\s*(>>?)?\s*\"?([^\s\"<>;|]+)\"?\s*<<-?\s*(['\"]?)(\w+)\3[^\n]*\n(.*?)\n\4[ \t]*(?=\n|$)",re.S)
HD2=re.compile(r"<<-?\s*(['\"]?)(\w+)\1\s*(?:>>?)\s*\"?([^\s\"<>;|]+)\"?[^\n]*\n(.*?)\n\2[ \t]*(?=\n|$)",re.S)
ASN=re.compile(r"(?:^|[;\n&(]|\s)([A-Z][A-Z0-9_]*)=(\"[^\"\n]*\"|'[^'\n]*'|[^\s;&|]+)")
def resolve(path,vars_):
    for _ in range(3):
        path=re.sub(r"\$\{?([A-Z][A-Z0-9_]*)\}?",lambda m: vars_.get(m.group(1),m.group(0)),path)
    return path
for tx in ["71f94277","a97ad692"]:
    uses={}
    for raw in open(f"{W}/raw_{tx}.jsonl"):
        d=json.loads(raw); k=d["kind"]; ts=d.get("ts"); ln=d["line"]
        if k=="tool_use":
            name=d["name"]; inp=d["input"] or {}; uses[d["id"]]=d
            if ts is None: continue
            if name in("Write","Edit","MultiEdit"):
                fp=inp.get("file_path","")
                if fp.startswith(ORCH):
                    if name=="Write": body=inp.get("content","")
                    else:
                        eds=inp.get("edits") or [inp]
                        body="".join(f"\n===== OLD =====\n{e.get('old_string','')}\n===== NEW =====\n{e.get('new_string','')}\n" for e in eds)
                    save(lane_of_path(fp),"written" if name=="Write" else "edits",ts,tx,ln,fp,os.path.basename(fp)+(".edit.md" if name!="Write" else ""),body)
            elif name=="Bash":
                cmd=inp.get("command","")
                if "orch_cd" not in cmd and not LABRE.search(cmd): continue
                vars_={"HOME":"/home/jjyeung"}
                for m in ASN.finditer(cmd): vars_[m.group(1)]=m.group(2).strip("\"'")
                got=False
                hits=[(m.group(2),m.group(3)=="",m.group(5)) for m in HD.finditer(cmd)]+[(m.group(3),m.group(1)=="",m.group(4)) for m in HD2.finditer(cmd)]
                for tgt,unq,body in hits:
                    rp=resolve(tgt,vars_)
                    if rp.startswith(ORCH):
                        if unq: body=body.replace("\\`","`").replace("\\$","$")
                        save(lane_of_path(rp),"written",ts,tx,ln,rp,os.path.basename(rp),body,extra=("heredoc_unquoted(vars_unexpanded)" if unq else "heredoc_quoted")); got=True
                ls=lanes_in(cmd)
                if (got or re.search(r"(>|tee |cp |mv |python|sed -i)",cmd)) and ORCH[:-1] in resolve(cmd,vars_):
                    for L in (ls or ["_other/_cmds"]):
                        save(L,"commands",ts,tx,ln,"(bash command)","cmd.sh",cmd)
            elif name in("Agent","Task","SendMessage"):
                s=json.dumps(inp,ensure_ascii=False,indent=1)
                for L in lanes_in(s): save(L,"agent_prompts",ts,tx,ln,"(agent prompt)",name+".md",s)
        elif k=="tool_result":
            u=uses.get(d["id"]); txt=d.get("text","")
            if u is not None and u.get("ts") is None: continue
            src=json.dumps(u["input"]) if u else ""
            ls=lanes_in(txt)
            if not ls: continue
            if not re.search(r"(RESULT|STATUS|QUESTION|BLOCKER|VERDICT|[Vv]erdict|REVIEW|READY|NO-GO|REPORT|events/)",txt): continue
            for L in ls: save(L,"results",ts,tx,ln,(u or {}).get("name","?")+":"+src[:300].replace("\t"," ").replace("\n"," "),"result.txt",(("TOOL INPUT:\n"+src[:4000]+"\n\nTOOL RESULT:\n") if u else "")+txt)
        elif k=="text":
            txt=d.get("text",""); ls=lanes_in(txt)
            if not ls or ts is None: continue
            role=d.get("role") or "x"
            for L in ls: save(L,"messages_"+str(role),ts,tx,ln,"(chat text)",f"{role}.md",txt)
index.sort(key=lambda r:(r[0],r[2],r[3],int(r[4])))
with open(os.path.join(OUT,"INDEX.tsv"),"w") as f:
    f.write("lane\tkind\tutc\ttranscript\tline\toriginal_path\trecovered_path\tbytes\tsha256_16\n")
    for r in index: f.write("\t".join(r)+"\n")
with open(os.path.join(OUT,"EXCLUDED_CREDENTIAL_ITEMS.tsv"),"w") as f:
    f.write("lane\tkind\tutc\ttranscript\tline\toriginal_path\n")
    for r in excluded: f.write("\t".join(map(str,r))+"\n")
per=collections.defaultdict(dict)
for (l,k),n in counts.items(): per[l][k]=n
json.dump(per,open(os.path.join(OUT,"COUNTS.json"),"w"),indent=1,sort_keys=True)
for l in sorted(per):
    if not l.startswith("_other"): print(l,per[l])
print("other dirs",sum(sum(v.values()) for l,v in per.items() if l.startswith("_other")),"excluded",len(excluded),"total",len(index))
