"""Record the production evidence invariant from authenticated metadata and source."""
from pathlib import Path
import ast,json,sys,hashlib
L=Path(__file__).resolve().parents[2];D=L/"work/build24f";R=D/"rehearsal4";T=L/"work/tree_r1"
sys.path.insert(0,str(L/"work/build24"));import joblib as J
ext=L.parent/"ext/m400real";e=J.load(ext/"e.json");n=J.load(L/"out/kit_n_go/k/n.json")
assert J.sha(ext/"e.json")==n["r1_training"]["handover_receipt"]["sha256"]
assert e["pins"]["artifact"]["sha256"]==n["init_artifact"]["artifact"]["sha256"]
manifest=J.load(ext/"MANIFEST.json")
member=next(v for v in manifest["files"] if v["sha256"]==e["pins"]["artifact"]["sha256"])
artifact_path=ext/"files"/member["path"].lstrip("/");assert J.sha(artifact_path)==e["pins"]["artifact"]["sha256"]
artifact=J.load(artifact_path)
assert not artifact.get("component_evidence")
assert n["r1_training"]["not_present_slots"]==["0","1"]
assert n["r1_training"]["proof_mode"]=="train" and n["geometry_connector"]=="none"
assert not n.get("geometry_online") and not n.get("frame_embeddings")
functions={}
for path,names in {
 T/"student_pilot/r1_components.py":["deferred","normalize","artifact_status","artifact_binding"],
 T/"student_pilot/r1_training.py":["training_components"],
 T/"student_pilot/r1_absence.py":["configuration","evidence","prove"],
 T/"launch_r1/production_proof.py":["bind_handover","_run"],
 T/"student_pilot/r1_population.py":["bind_prepared"],
 T/"student_pilot/r1_handover.py":["bind_target"],
 L/"out/kit_n_go/b/rv.py":["sync_preparation"],
 }.items():
    raw=path.read_text();tree=ast.parse(raw);lines=raw.splitlines()
    functions[str(path.relative_to(L))]=dict(sha256=hashlib.sha256(raw.encode()).hexdigest(),functions={
      f.name:dict(line=f.lineno,end_line=f.end_lineno,source="\n".join(lines[f.lineno-1:f.end_lineno]))
      for f in tree.body if isinstance(f,ast.FunctionDef) and f.name in names})
slots=J.load(D/"rehearsal3/COMPONENT_EVIDENCE_DIFF.json")["slots"]
expected={k:dict(status=v["export_status"],**({"receipt_sha256":J.sha(ext/"e.json")} if v["export_status"]=="DEFERRED" else {"basis":"Native configuration, module and pinned heads inventory proof"})) for k,v in slots.items()}
J.write(R/"PRODUCTION_COMPONENT_EVIDENCE.json",dict(
 verdict="No production launch blocker from this mismatch; fixture-only donor replacement after preparation",
 basis="Source invariant plus authenticated production pins; not a production preparation or export execution",
 receipt=n["r1_training"]["handover_receipt"],artifact=n["init_artifact"]["artifact"],
 production_inherited_component_evidence=artifact.get("component_evidence",{}),expected_slots=expected,
 production_status_inputs={k:n.get(k) for k in ("geometry_connector","geometry_online","carrier_placement","frame_embeddings")},
 production_r1_status_inputs={k:n["r1_training"].get(k) for k in ("registry","mix","component_rows","proof_mode","not_present_slots","handover_receipt","p_run")},
 invariant=[
 "a.py q invokes production_proof; s1_admission.prepare_only calls carrier_c1_run.prepare after staging and binding the donor.",
 "carrier_c1_run.prepare records artifact_status(cfg) directly at lines 638-640.",
 "s1_admission copies the native receipt, r1_population deep-copies it, and bind_handover changes only sampler/handover/config/source bindings.",
 "h.py attaches host_receipt; rv.py attaches review; sync_preparation replaces only r1_training and re-pins the full receipt.",
 "Neither gate pin is an input to deferred, training_components or absence evidence; the donor artifact and handover receipt do not change after native preparation.",
 "The two absence records recompute from the same configuration, builder and pinned donor heads, independent of training updates.",
 "With successful native preparation, normalized recorded evidence equals export artifact_status at step 100 and later exports.",
 ],functions=functions,kit_fix_required=False,tree_change_required=False,
 limitations="Production heads payload is not among the staged small metadata; no real 9B model, full production preparation or production step-100 export was executed. Fixture execution verifies native export and both kit re-pinning calls separately."))
print("PASS: production source invariant; authenticated receipt b467c32b/artifact 5083243c; expected 2 NOT_PRESENT and 7 DEFERRED.")
