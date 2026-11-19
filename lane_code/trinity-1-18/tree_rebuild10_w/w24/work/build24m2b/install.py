from common import *
for name in ("q","n","n_go","qd"):
 k=kit(name)
 replace(k/"b/sv.py",(D/"sv.py").read_bytes())
 p=k/"b/ep.py";s=p.read_text().replace("target.resolve().is_relative_to(p)","(target.resolve()==p or p in target.resolve().parents)")
 s=s.replace("    return record\n","    publish_artifacts(target, root)\n    return record\n")
 marker="\n\nif __name__=='__main__':"
 helper=(D/"artifacts.py").read_text()
 s=s.replace(marker,"\n\n"+helper+marker)
 replace(p,s)
 p=k/"b/rv.py";s=p.read_text();needle="        canonical,_=authority.canonical(row)\n        if not canonical:raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED')"
 assert needle in s
 s=s.replace(needle,"        canonical,_=authority.canonical(row)\n        if not canonical:canonical=(row.get('provenance') or {}).get('canonical_scene')\n        if not canonical:raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED')")
 replace(p,s)
 print(name,reseal(k))
k=kit("qd")
for doc in ("k/a.json","BUILD.json"):
 v=J.load(k/doc);v.update(discovery=True,claims="nothing",GO=False)
 v["resource_request"]=dict(partition="preempt",gpus=1,cpus=48,memory="800G",time="04:00:00",requeue=False)
 cap(k,doc,v)
print("qd",reseal(k))
