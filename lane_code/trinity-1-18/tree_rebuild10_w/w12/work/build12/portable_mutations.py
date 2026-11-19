from pathlib import Path
import ast,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
p=Path('/scratch/jjyeung/orch_n30/review_treen1/work/s3/mut.py')
node=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='M' for t in n.targets))
space={'H':'student_pilot/r1_handover.py','RT':'student_pilot/r1_training.py','E':'launch_r1/entry.py'}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),space)
(B/'proofs/review_inputs/MUTATION_SPEC.json').write_text(json.dumps(dict(source=str(p),
    source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mutations=space['M']),indent=2))
