"""Rebind fixture evidence after donor publication; reuse immutable prepared assets."""
from pathlib import Path
from copy import deepcopy
import os,sys,subprocess,json
L=Path(__file__).resolve().parents[2];D=L/"work/build24f";old=D/"rehearsal3";R=D/"rehearsal4";ns=Path("/tmp/q_22c714e1")
sys.path[:0]=[str(L/"work/build24"),str(L/"work/tree_r1")]
import joblib as J
if "--inside" not in sys.argv:
    assert not R.exists(), "Preserve any existing rehearsal4 attempt"
    R.mkdir();(R/"tmp").mkdir()
    # Copy only small launch metadata. Trees, weights, databases and failed outputs stay in place.
    names=("v.json","prepared.json","admission.json","authorization.json","host.json","review.json","r.json","r2.json","rooms.json","PREPARED.json")
    for name in names:
        p=old/name;assert p.stat().st_size<10_000_000
        (R/name).write_bytes(p.read_bytes())
    stages=J.load(old/"STAGES.json")
    stages=[dict(v,reused_from=str(old)) for v in stages if v["stage"] in ("canary","rooms","v_config","fixture_gates")]
    assert len(stages)==4 and all(v["returncode"]==0 for v in stages)
    J.write(R/"STAGES.json",stages)
    args=J.load(old/"VIEW.json")
    for i in range(len(args)-2):
        if args[i]=="--bind" and args[i+1]==str(old):args[i]="--ro-bind"
    args += ["--bind",str(R),str(R),"--bind",str(R),str(ns),
             "--ro-bind",str(old/"p2"),str(ns/"p2"),
             "--ro-bind",str(L/"work/build24d/go/p"),str(ns/"p"),
             "--ro-bind",str(old/"p2/s"),str(L/"work/tree_r1")]
    J.write(R/"VIEW.json",args)
    env={**os.environ,"TMPDIR":str(R/"tmp"),"S1_CPU_REHEARSAL":"1","S1_REHEARSAL_ATTEMPT":"b24f_fresh"}
    subprocess.run(args+[sys.executable,"-I","-s","-B",str(Path(__file__).resolve()),"--inside"],env=env,check=True)
    print("PASS: rehearsal4 preparation and admission pins bind the final donor evidence; shared assets are read-only.")
    raise SystemExit
import torch
torch.set_num_threads(2);torch.set_num_interop_threads(1)
from student_pilot import r1_components as C,r1_persisted as P
from student_pilot.p3_provenance import load,pinned,file_pin,digest
from student_pilot.carrier_c1_run import identity
cfg=J.load(ns/"v.json");initial=deepcopy(cfg)
with P.scope(J.load(R/"r2.json")["_paths"]),P.scope(cfg["r1_training"]["persisted_files"]):
    prep=load(pinned(cfg["preparation"]));before=deepcopy(prep)
    prep["component_evidence"]=C.artifact_status(cfg)
    assert C.normalize(before["component_evidence"])!=prep["component_evidence"]
    cfg["preparation"]=J.write(ns/"prepared.json",prep)
    admission=load(pinned(cfg["admission"]));admission["preparation"]=cfg["preparation"]
    cfg["admission"]=J.write(ns/"admission.json",admission)
    assert identity(cfg)==identity(initial)
    assert C.artifact_binding(cfg,C.artifact_status(cfg))["component_preparation"]==cfg["preparation"]
    J.write(ns/"v.json",cfg)
    J.write(R/"FIXTURE_REBIND.json",dict(status="PASS",before_preparation=initial["preparation"],
        after_preparation=cfg["preparation"],before_admission=initial["admission"],after_admission=cfg["admission"],
        before_component_sha256=digest(before["component_evidence"]),after_component_sha256=digest(prep["component_evidence"]),
        config_identity=identity(cfg),shared_readonly_assets=[str(old/"p2"),str(old/"model"),str(old/"donor"),str(old/"rebind"),str(L/"work/build24d/go/p")],
        canary_reused=True,rows_and_weights_changed=False,distributed_training_executed=False))
