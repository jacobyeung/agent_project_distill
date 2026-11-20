from common import *
p=D/'namespace_test.py';s=p.read_text().replace("cmd[-3:]=[str(D/'p_probe.py'),str(D/'p_tree'),'/project/p0/s.json']",'''wrapper=D/'namespace_probe.py'
wrapper.write_text('import sys,runpy\\nsys.path[:0]='+repr(rb.environment()['paths'])+'\\nrunpy.run_path('+repr(str(D/'p_probe.py'))+',run_name="__main__")\\n')
cmd[-3:]=[str(wrapper),str(D/'p_tree'),'/project/p0/s.json']''');replace(p,s)
p=D/'namespace_test.log';p.rename(L/'attic/build24m4j/namespace_first.log')
