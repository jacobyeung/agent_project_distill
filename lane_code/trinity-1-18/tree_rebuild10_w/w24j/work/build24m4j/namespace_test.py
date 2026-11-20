import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sys.path.insert(0,str(kit('n')/'b'));import rb,subprocess
pin='5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'
mounts={'/project/p0/s.json':dict(source=str(input_file(pin)),sha256=pin)}
cmd=rb.command(D,D/'unused',D/'p_tree',mounts)
wrapper=D/'namespace_probe.py'
wrapper.write_text('import sys,runpy\nsys.path[:0]='+repr(rb.environment()['paths'])+'\nrunpy.run_path('+repr(str(D/'p_probe.py'))+',run_name="__main__")\n')
cmd[-3:]=[str(wrapper),str(D/'p_tree'),'/project/p0/s.json']
p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(D/'namespace.log').write_text(p.stdout)
J.write(D/'NAMESPACE_TEST.json',dict(returncode=p.returncode,output=p.stdout,command=cmd,scope='Real bwrap child, isolated Python, exact P file inventory and native implementation guards; logical input path bound to local staged bytes'))
print(p.stdout);assert p.returncode==0
