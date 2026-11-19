"""Compare native component evidence without running distributed training."""
from pathlib import Path
from copy import deepcopy
import json, sys, os, subprocess
L=Path(__file__).resolve().parents[2]; D=L/"work/build24f"; R=D/"rehearsal3"
sys.path[:0]=[str(L/"work/build24"),str(L/"work/tree_r1"),str(L/"out/kit_n_go/b")]
import joblib as J
if "--inside" not in sys.argv:
    args=J.load(R/"VIEW.json")
    subprocess.run(args+[sys.executable,"-I","-s","-B",str(Path(__file__).resolve()),"--inside"],check=True)
    raise SystemExit
import torch
torch.set_num_threads(2); torch.set_num_interop_threads(1)
from student_pilot import r1_components as C, r1_persisted as P
from student_pilot.p3_provenance import load,pinned,digest
from rv import sync_preparation

def difference(a,b,path=""):
    if isinstance(a,dict) and isinstance(b,dict):
        result=[]
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:result.append(dict(field=path+"/"+k,before=a.get(k),after=b.get(k)))
            else:result.extend(difference(a[k],b[k],path+"/"+k))
        return result
    return [] if a==b else [dict(field=path,before=a,after=b)]

cfg=load("/tmp/q_22c714e1/v.json")
aliases=J.load(R/"r2.json")["_paths"]
with P.scope(aliases),P.scope(cfg["r1_training"]["persisted_files"]):
    prep=load(pinned(cfg["preparation"]))
    before=C.normalize(prep.get("component_evidence",{})); after=C.artifact_status(cfg)
    changes=difference(before,after)
    try:C.artifact_binding(cfg,after)
    except ValueError as e:refusal=str(e)
    else:raise AssertionError("Expected the observed export refusal")
    assert refusal=="COMPONENT_EVIDENCE_PREPARATION_MISMATCH:export"
    chain={}
    for name in ("p2/ph.json","rebind/h/receipt.json"):
        p=R/name; v=load(p)
        chain[name]=dict(sha256=J.sha(p),component_evidence_sha256=digest(v["component_evidence"]),equal_to_final=v["component_evidence"]==prep["component_evidence"])
    native=load(pinned(prep["native_preparation"]))
    chain[prep["native_preparation"]["path"]]=dict(component_evidence_sha256=digest(native["component_evidence"]),equal_to_final=native["component_evidence"]==prep["component_evidence"])
    test=deepcopy(cfg); sync_preparation(test,R,"COMPONENT_SYNC_TEST.json")
    sync=load(pinned(test["preparation"]))
    assert sync["component_evidence"]==prep["component_evidence"]
    report=dict(preparation=cfg["preparation"],physical_preparation=str(R/"prepared.json"),
        recorded=before,artifact_status=after,changes=changes,refusal=refusal,chain=chain,
        slots={k:dict(recorded_status=before[k]["status"],export_status=after[k]["status"],equal=before[k]==after[k]) for k in sorted(after)},
        sync_preparation_preserves_component_evidence=True,
        final_handover_receipt=cfg["r1_training"]["handover_receipt"],init_artifact=cfg["init_artifact"]["artifact"])
    J.write(R/"COMPONENT_EVIDENCE_DIFF.json",report)
    print(json.dumps({k:report[k] for k in ("preparation","changes","slots","chain")},indent=2))
