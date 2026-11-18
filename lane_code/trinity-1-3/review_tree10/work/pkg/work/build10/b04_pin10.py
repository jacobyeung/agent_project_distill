from pathlib import Path
import ast,hashlib,inspect,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.geometry_profiles import GeometryContract
source=inspect.getsource(GeometryContract.validate);actual=hashlib.sha256(source.encode()).hexdigest()
file=B/'b04_stage/e2e_reader/geometry.py'
parsed=ast.parse(file.read_text())
expected=next(n.value.value for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SEALED_VALIDATE_SHA256' for t in n.targets))
prior=L.parent/'w9f/work/tree_r1/student_pilot/geometry_profiles.py';current=L/'work/tree_r1/student_pilot/geometry_profiles.py'
record=dict(expected=expected,actual=actual,match=expected==actual,
    b04_source='work/build10/b04_stage/e2e_reader/geometry.py:19',
    tree_source='work/tree_r1/student_pilot/geometry_profiles.py',
    validator_line=GeometryContract.validate.__code__.co_firstlineno,
    file_identical_to_9fix=hashlib.sha256(current.read_bytes()).hexdigest()==hashlib.sha256(prior.read_bytes()).hexdigest())
(B/'B04_VALIDATOR_PIN.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
