from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import runpy,sys
L=Path(__file__).resolve().parents[2]
t=SimpleNamespace(__version__='2.11.0+cu129',cuda=SimpleNamespace(is_available=lambda:True,device_count=lambda:1,
 get_device_properties=lambda index:SimpleNamespace(name='NVIDIA H100 80GB HBM3',total_memory=85520809984)))
with patch.dict(sys.modules,torch=t):runpy.run_path(str(L/'work/build21/kits/q/b/g.py'),run_name='__main__')
