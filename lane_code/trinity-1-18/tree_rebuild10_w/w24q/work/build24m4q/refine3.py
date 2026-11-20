import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
p=L/'out/rcj/ch.py';s=p.read_text().replace("for name, owner, attribute in (", "for name, owner, attribute, function in (")
for owner,attr in [('r1_coverage.WordingExclusion','check'),('row_text_audit','check'),('extent_receipt.Extents','check'),('r1_training','row_check'),('r0_exclusion.Reserve','check'),('r2_contract.Admission','check')]:
 s=s.replace(owner+", '"+attr+"')",owner+", '"+attr+"', "+owner+'.'+attr+')')
s=s.replace('getattr(owner, attribute)','function');replace(p,s)
p=D/'assets.py';s=p.read_text().replace('Qwen2VLProcessor','CLIPProcessor').replace('Qwen2VLImageProcessorPil','CLIPImageProcessorPil').replace("model_type='qwen2_vl'","model_type='clip'").replace("root=D/'assets';root.mkdir()", "root=D/'assets2';root.mkdir()")
replace(p,s)
