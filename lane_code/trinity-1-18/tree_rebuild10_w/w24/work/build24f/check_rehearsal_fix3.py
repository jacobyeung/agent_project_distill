"""Check export binding and kit re-pinning on the repaired single-process fixture."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,subprocess,tempfile
L=Path(__file__).resolve().parents[2];D=L/"work/build24f";R=D/"rehearsal4";old=D/"rehearsal3";ns=Path("/tmp/q_22c714e1")
sys.path[:0]=[str(D),str(L/"work/build24"),str(L/"work/tree_r1"),str(L/"work/build21"),str(L/"out/kit_n_go/b")]
import joblib as J
if "--inside" not in sys.argv:
    env={**os.environ,"TMPDIR":str(R/"tmp"),"S1_CPU_REHEARSAL":"1","S1_REHEARSAL_ATTEMPT":"b24f_fresh",
         "CUDA_VISIBLE_DEVICES":"","OMP_NUM_THREADS":"2","MKL_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2",
         "HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","PYTHONDONTWRITEBYTECODE":"1"}
    raise SystemExit(subprocess.run(J.load(R/"VIEW.json")+[sys.executable,"-I","-s","-B",str(Path(__file__).resolve()),"--inside"],env=env).returncode)
import native24 as N
tempfile.tempdir=str(R/"tmp");N.torch.set_num_threads(2)
from student_pilot import r1_components as C,r1_persisted as P,r1_handover as H
from student_pilot import r1_rooms as Rooms,r1_direction_twins as Twins
from student_pilot.p3_provenance import load,pinned,digest,file_pin
from launch_r1 import entry
from rv import sync_preparation
syn=load(L/"work/build24/proofs/capacity/TWIN_BOUNDARY.json")["pins"]
Twins.ROWS=syn["rows"]["sha256"];Twins.BINDING=syn["binding"]["sha256"];Twins.ALIASES=syn["aliases"]["sha256"];Rooms.STORE=syn["source_database"]["sha256"]
N.C.processor_for=N.processor
cfg=J.load(ns/"v.json");records=[]
with P.scope(J.load(R/"r2.json")["_paths"]),P.scope(cfg["r1_training"]["persisted_files"]):
    current=C.artifact_status(cfg);prep=load(pinned(cfg["preparation"]))
    assert C.normalize(prep["component_evidence"])==current
    assert sum(v["status"]=="DEFERRED" for v in current.values())==7
    assert sum(v["status"]=="NOT_PRESENT" for v in current.values())==2
    binding=C.artifact_binding(cfg,current)
    assert entry.admit(cfg)==0
    assert N.C.identity(cfg)==N.C.identity(load(pinned(J.load(ns/"p2/q/RESULT.json")["config"])))
    receipt,manifest=N.C.prepared(cfg,admission=True)
    # Exercise the exact shared helper used by h.py and rv.py after each new receipt pin.
    for field in ("host_receipt","review"):
        test=deepcopy(cfg);test["r1_training"][field]=J.write(R/("SYNC_"+field+".json"),{"probe":"receipt pin only"})
        sync_preparation(test,R,"SYNC_PREP_"+field+".json")
        observed=C.artifact_status(test)
        assert observed==current
        assert load(pinned(test["preparation"]))["component_evidence"]==current
        C.artifact_binding(test,observed)
        records.append(dict(stage=field+"_sync",status="PASS",unchanged_component_sha256=digest(observed)))
    # A stale receipt still refuses through the unmodified native export gate.
    stale=deepcopy(cfg);stale["preparation"]=file_pin(old/"prepared.json")
    try:C.artifact_binding(stale,current)
    except ValueError as e:
        assert str(e)=="COMPONENT_EVIDENCE_PREPARATION_MISMATCH:export"
        records.append(dict(mutation="stale preparation",refusal=str(e)))
    else:raise AssertionError("Stale evidence must refuse")
    from rehearsal_model import install
    install(N.C)
    model=N.C.load_model(manifest,receipt,N.C.processor_for_receipt(manifest,receipt))
    groups=H.verify_trainable_groups(cfg,model);assert groups["source"]==groups["target"]
    optimizer=N.torch.optim.AdamW(N.C.parameter_groups(model))
    # Local collectives stand in for the distributed transport only; native export writes all metadata.
    with N.RunnerTests().local_collectives(),patch("student_pilot.fsdp_training.publication_state",return_value=model.state_dict()):
        N.C.export(R/"export_probe",model,model,cfg,2,optimizer=optimizer)
    artifact=J.load(R/"export_probe/artifact.json")
    assert artifact["component_evidence"]==current
    assert artifact["component_preparation"]==cfg["preparation"]
    assert artifact["component_evidence_sha256"]==digest(current)
    try:C.guard(artifact,["VSI-Bench"],"fixture-official-check")
    except ValueError as e:
        assert str(e).startswith("COMPONENT_EVIDENCE_DEFERRED:")
        records.append(dict(mutation="official read",refusal=str(e)))
    else:raise AssertionError("Official read must refuse")
    J.write(R/"FIX3_VALIDATION.json",dict(status="PASS",preparation=cfg["preparation"],
        native_artifact_binding=binding,native_entry_admit=True,native_prepared=True,native_group_check=True,
        native_export=file_pin(R/"export_probe/artifact.json"),records=records,
        component_status={k:v["status"] for k,v in current.items()},component_evidence_sha256=digest(current),
        single_process=True,training_steps=0,distributed_training_executed=False,
        boundaries="Existing tiny model, synthetic stores/processor/frame host; local collectives and state publication for unwrapped export"))
print("PASS: entry, prepared, groups, native export, host/review re-pinning; stale preparation and official read refuse; no training.")
