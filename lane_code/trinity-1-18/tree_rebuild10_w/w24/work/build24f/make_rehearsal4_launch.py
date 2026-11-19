"""Select the repaired fixture and its preserved source snapshot."""
from pathlib import Path
import json,ast
D=Path(__file__).resolve().parent
assert json.loads((D/"rehearsal4/FIX3_VALIDATION.json").read_text())["status"]=="PASS"
changes=[]
for name in ("rehearsal_runner.py","rehearsal_boundary.py","rehearsal_copier.py","check_rehearsal.py","rehearsal_repro.py","go_rehearsal.sh"):
    p=D/name;before=p.read_text()
    after=before.replace("D/'rehearsal3'","D/'rehearsal4'").replace("D/'rehearsal3/tmp'","D/'rehearsal4/tmp'").replace("build24f/rehearsal3/","build24f/rehearsal4/")
    if name=="rehearsal_runner.py":
        after=after.replace("assert v['tree']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']",
            "cfg=J.load(root/'v.json')\n        assert v['tree']==J.load(cfg['code']['path'])['tree_sha256']")
    if name=="rehearsal_repro.py":
        after=after.replace("str(L/'work/tree_r1')","str(D/'rehearsal3/p2/s')")
    if name.endswith(".py"):ast.parse(after,filename=name)
    p.write_text(after)
    changes.append(dict(path=name,before=before,after=after))
p=D/"rehearsal_preserve_metadata.py";before=p.read_text()
needle="    target=rebind(load(pinned(result['config'])))\n"
assert needle in before
after=before.replace(needle,needle+"    # A donor receipt change also changes DEFERRED evidence recorded by preparation.\n    from student_pilot.r1_components import artifact_status\n    with P.scope(paths):\n        prepared=load(pinned(target['preparation']))\n        prepared['component_evidence']=artifact_status(target)\n        target['preparation']=J.write(R/'rebind/component_preparation.json',prepared)\n")
ast.parse(after);p.write_text(after);changes.append(dict(path=p.name,before=before,after=after))
p=D/"REHEARSAL_OVERRIDES.json";v=json.loads(p.read_text());before=json.loads(p.read_text());v["copier"]["target"]="rehearsal4/target"
v["component_preparation"]=dict(producer="student_pilot.r1_components.artifact_status",when="After the final fixture donor export and receipt are bound",changed_slots="Seven DEFERRED receipt_sha256 fields",physical_output_root=str(D/"rehearsal4"),source_snapshot=str(D/"rehearsal3/p2/s"),shared_assets="Read-only existing model, donor and prepared stores")
p.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
changes.append(dict(path=p.name,before=before,after=v))
(D/"rehearsal4/LAUNCH_CHANGES.json").write_text(json.dumps(changes,indent=2)+"\n")
print("Selected rehearsal4; the rehearsal view mounts the authenticated source snapshot read-only.")
