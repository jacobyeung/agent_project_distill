mkdir -p /scratch/jjyeung/orch_n30/n_review/r1b
cat > /scratch/jjyeung/orch_n30/n_review/r1b/fh.py <<'P'
import ast,hashlib,sys,json
from pathlib import Path
FUN={'launch_r1/entry.py':['admit'],'student_pilot/carrier_c1_run.py':['identity','prepare','prepared','train'],'student_pilot/r2_scene_bindings.py':['rebuild','verify','rebuild_pool','rebuild_receipt','populations'],'student_pilot/s1_routing.py':['build','_build']}
FILES=['student_pilot/carrier_c1_data.py','student_pilot/carrier_c1.py','student_pilot/carrier_c1_run.py','launch_r1/entry.py','student_pilot/r1_components.py','student_pilot/r1_rooms.py','student_pilot/r1_coverage.py','student_pilot/r2_scene_bindings.py','student_pilot/r2_contract.py','student_pilot/s1_routing.py','student_pilot/s1_admission.py','student_pilot/r1_handover.py','launch_r1/production_proof.py','student_pilot/r1_persisted.py','student_pilot/r1_training.py','student_pilot/r1_direction_twins.py','student_pilot/r1_loader.py','student_pilot/r1_population.py','student_pilot/r2_withheld.py','student_pilot/s1_exclusions.py','student_pilot/row_removals.py']
out={}
for t in sys.argv[1:]:
  r={}
  for f in FILES:
    p=Path(t)/f
    r[f]=hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None
  for f,names in FUN.items():
    p=Path(t)/f
    if not p.exists(): continue
    src=p.read_text(); tree=ast.parse(src)
    for n in tree.body:
      if isinstance(n,(ast.FunctionDef,)) and n.name in names:
        r[f+'::'+n.name]=hashlib.sha256(ast.get_source_segment(src,n).encode()).hexdigest()[:16]
  out[t]=r
print(json.dumps(out,indent=0))
P
cd /scratch/jjyeung/orch_n30/n_review && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B r1b/fh.py /scratch/jjyeung/orch_n30/n_review/tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1
echo "== tree copy seal"; cd /scratch/jjyeung/orch_n30/n_review/tree && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"
