import sqlite3,json,re,collections,random
c=sqlite3.connect("file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?immutable=1",uri=True)
pairs=collections.defaultdict(list)
for i,row in c.execute("select i,row from rows where i<195471 and row like '%pair_id%'"):
  r=json.loads(row)
  if r.get("facing") in("away","toward"): pairs[r["pair_id"]].append((i,r["facing"],r["qid"],r["answer"],r["student_input"]["question"],r["student_input"]["options"],r["question_type"]))
new=[json.loads(l) for l in open("new_rows.jsonl")]; new=[x for x in new if x["row"]["pool"]=="r1_away_opp"]
def opt(r):
  return {o.split(". ",1)[0]:o.split(". ",1)[1] for o in r["student_input"]["options"]}
def fwd(t):
  m=re.search(r"would be (.*?)\.\n",t); return m.group(1) if m else None
HARD={"in front of me, on my left":"back-right","in front of me, on my right":"back-left","behind me, on my left":"front-right","behind me, on my right":"front-left"}
MED={"ahead of me, slightly to my left":"back","ahead of me, slightly to my right":"back","out to my left":"right","out to my right":"left","behind me, on my left":"right","behind me, on my right":"left"}
EASY={"to my left":"right","to my right":"left"}
bad=[];stats=collections.Counter();ans=collections.Counter();tw=collections.Counter()
for x in new:
  r=x["row"];qt=r["question_type"].split("_")[-1];f=fwd(r["target"]);a=opt(r)[r["answer"]]
  exp={"easy":EASY,"medium":MED,"hard":HARD}[qt].get(f)
  if exp!=a: bad.append((x["i"],qt,f,a))
  if "That is a half turn" not in r["target"] or "facing in the opposite direction of" not in r["student_input"]["question"]: bad.append((x["i"],"noturn"))
  concl=[s for s in r["target"].split("\n") if s.startswith("So ")][0]
  if not concl.rstrip(".").endswith(a): bad.append((x["i"],"concl",concl,a))
  ans[(qt,a)]+=1
  P=pairs[r["pair_id"]]; fac=collections.Counter(p[1] for p in P); tw[(qt,tuple(sorted(fac.items())))]+=1
  src=[p for p in P if p[2]==r["provenance"]["rendering"]["derived_from_v6_qid"]]
  if not src or src[0][3]!=r["answer"] or src[0][5]!=r["student_input"]["options"]: bad.append((x["i"],"src",src[:1]))
  tow=[p for p in P if p[1]=="toward"]
  if tow:
    to={o.split(". ",1)[0]:o.split(". ",1)[1] for o in tow[0][5]}[tow[0][3]]; stats[(qt,"toward="+to,"away="+a)]+=1
print("bad",len(bad),bad[:10]); print("twins",tw)
for k in sorted(ans): print("ANS",k,ans[k])
for k in sorted(stats): print("TT",k,stats[k])
# v6 away/toward answer priors per type
pri=collections.Counter()
for pid,P in pairs.items():
  for p in P:
    to={o.split(". ",1)[0]:o.split(". ",1)[1] for o in p[5]}[p[3]]; pri[(p[6].split("_")[-1],p[1],to)]+=1
for k in sorted(pri): print("V6",k,pri[k])
random.seed(20261117)
by=collections.defaultdict(list)
for x in new: by[x["row"]["question_type"]].append(x)
samp=[s for k in sorted(by) for s in random.sample(by[k],7)][:20]
with open("away_sample20.md","w") as f:
  for x in samp:
    r=x["row"]; f.write(f"## i={x['i']} {r['qid']} {r['question_type']} ans={r['answer']} {opt(r)[r['answer']]}\nQ: {r['student_input']['question']} {r['student_input']['options']}\n{r['target']}\n\n")
