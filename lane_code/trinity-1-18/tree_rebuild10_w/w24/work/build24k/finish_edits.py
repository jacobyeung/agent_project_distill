from pathlib import Path
import ast
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
p=D/'sequence_final.py';s=p.read_text().replace('sequence_verified','sequence_completed').replace("__import__('os').link(item['local_path'],source_root/item['sha256'])", "shutil.copyfile(item['local_path'],source_root/item['sha256'])");p.write_text(s)
p=D/'go_rehearsal_k.sh';p.write_text(p.read_text().replace('work/build24f/rehearsal4/tmp','work/build24k/rehearsal_k/tmp'))
p=D/'rehearsal_boundary.py';p.write_text(p.read_text().replace("D/'rehearsal4/tmp'","D/'rehearsal_k/tmp'"))
p=D/'rehearsal_repro.py';p.write_text(p.read_text().replace("D/'rehearsal3/p2/s'","L/'work/tree_r1'"))
p=D/'make_rehearsal_k.py';p.write_text(p.read_text().replace("for key in ('preparation','authorization','admission'):","for key in ('preparation','authorization','admission','readout'):"))
p=D/'rehearsal_model.py';s=p.read_text().replace("D = Path(__file__).resolve().parent", "D = Path(__file__).resolve().parent\nSOURCE=D.parent/'build24f/rehearsal3'\nif not SOURCE.exists():SOURCE=D.parent/'build24f/rehearsal2'").replace("D.parent/'build24f/rehearsal3/model.json'", "SOURCE/'model.json'");p.write_text(s)
for p in D.glob('*.py'):ast.parse(p.read_text())
print('Scripts parsed; GO rehearsal remains unexecuted')
