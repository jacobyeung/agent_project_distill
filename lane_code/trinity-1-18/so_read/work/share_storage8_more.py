from pathlib import Path
import json,runpy
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/checks/STORAGE8.json'
before=json.loads(p.read_text())
runpy.run_path(str(L/'work/share_storage8.py'),run_name='__main__')
after=json.loads(p.read_text())
for key in ('changed_files','unique_bytes_shared','read_bytes'):after[key]+=before[key]
after['passes']=before.get('passes',1)+1
after['scope']='completed pre-task fixtures only; replacements checked byte-for-byte; each pass bounded to 100 MB local candidate reads'
p.write_text(json.dumps(after,sort_keys=True,indent=2)+'\n')
print('Cumulative:',json.dumps(after,sort_keys=True))
