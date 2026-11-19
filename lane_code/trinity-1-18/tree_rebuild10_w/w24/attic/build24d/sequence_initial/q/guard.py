import runpy,sys
import torch
from types import SimpleNamespace
torch.cuda.is_available=lambda:True
torch.cuda.device_count=lambda:1
torch.cuda.get_device_properties=lambda i:SimpleNamespace(name='CPU fixture',total_memory=85017493504)
runpy.run_path(sys.argv[1],run_name='__main__')
