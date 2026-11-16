from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
import sys,json,traceback
B=Path(__file__).resolve().parents[1];OLD=B.parent/'03_vsti_c';sys.path.append(str(B/'code'))
from adapter import dump,pin
import o
current=o.imports()[2]
p=OLD/'code/sj/orch_cd/evalx/work/milestone/orchard_results.py'
spec=spec_from_file_location('v1c_return_diagnosis',p);old=module_from_spec(spec);spec.loader.exec_module(old)
rows=[]
for token in ('5d648e9274d54fba92aef108','9ea1cfc0b79848029c0e53d4','ad648e9274d54fba92aef108'):
 row=dict(token=token,packet_admits=bool(o.re.fullmatch('[a-f0-9]{24,32}',token)))
 try:old.identity(old.AUTHORIZED_POOL,token);row['v1c']='accepted'
 except ValueError as e:row['v1c']=str(e);row['v1c_traceback']=traceback.format_exc()
 row['v1f']=str(current.identity(current.AUTHORIZED_POOL,token));rows.append(row)
dump(B/'out/TOKEN_REPRO.json',dict(source=pin(p),results=rows,remote_IO=False,job_170228_token='not supplied'))
