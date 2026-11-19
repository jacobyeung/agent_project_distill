import runpy,sys
from types import SimpleNamespace
sys.modules['torch']=SimpleNamespace(__version__='cpu-fixture',cuda=SimpleNamespace(is_available=lambda:True,device_count=lambda:1,get_device_properties=lambda i:SimpleNamespace(name='CPU fixture',total_memory=85017493504)))
runpy.run_path(sys.argv[1],run_name='__main__')
