import json,numpy as np,collections,random,os,itertools
new=[json.loads(l) for l in open("new_rows.jsonl")]; room=[x for x in new if x["row"]["pool"]=="r1_room_traced"]
bad=[];shares=[];maxshare=[];cache={}
for x in room:
  r=x["row"];rt=r["provenance"]["room_trace"];p=rt["raster_path"]
  if not os.path.exists(p): bad.append((x["i"],"noraster"));continue
  z=np.load(p);inst=z["inst"];ids=list(z["ids"]);labels=[str(s) for s in z["labels"]]
  if list(z["frame_indices"])!=r["student_input"]["frame_indices"]: bad.append((x["i"],"pins"))
  for L in rt["landmarks"]:
    j=ids.index(L["instance_id"])
    if " ".join(labels[j].lower().split())!=L["label"]: bad.append((x["i"],"label",labels[j],L["label"]))
    if not np.allclose(z["obb_centroid"][j],L["centroid"]): bad.append((x["i"],"centroid"))
    sh=[(inst[f]==L["instance_id"]).mean() for f in range(32)]
    fs=next((f+1 for f in range(32) if sh[f]>=.002),None)
    if fs!=L["first_seen"]: bad.append((x["i"],"first_seen",L["label"],fs,L["first_seen"]))
    if f"{L['label']} in frame {L['first_seen']}" not in r["target"] and f"{L['label']} first seen in frame {L['first_seen']}" not in r["target"]: bad.append((x["i"],"text",L["label"]))
    shares.append(sh[L["first_seen"]-1]); maxshare.append(max(sh))
  # relate recompute
  up=rt["up_axis"];hor=[k for k in range(3) if k!=up];C=np.array([L["centroid"] for L in rt["landmarks"]])[:,hor]
  a,c=max(itertools.combinations(range(len(C)),2),key=lambda ij:np.linalg.norm(C[ij[0]]-C[ij[1]]))
  if [a,c]!=rt["relate"]["pair"]: bad.append((x["i"],"pair"))
  # up axis sanity: floor height below camera
  if r["answer"]!=r["provenance"]["source_answer"]: bad.append((x["i"],"answer"))
  if not r["target"].endswith("\n\n"+r["answer"]): bad.append((x["i"],"tail"))
shares=np.array(shares);maxshare=np.array(maxshare)
print("bad",len(bad),bad[:15])
print("landmarks",len(shares),"cited-frame share quantiles",np.quantile(shares,[.1,.25,.5,.75,.9]).round(4),"frac<0.01",(shares<.01).mean().round(3),"frac<0.005",(shares<.005).mean().round(3))
print("max share over pins quantiles",np.quantile(maxshare,[.1,.5,.9]).round(4))
lab=collections.Counter(L["label"] for x in room for L in x["row"]["provenance"]["room_trace"]["landmarks"]); print(lab.most_common(40))
