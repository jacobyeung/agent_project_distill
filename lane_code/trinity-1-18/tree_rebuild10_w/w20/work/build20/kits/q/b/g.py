import torch
if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 80*(1<<30):
 raise RuntimeError('E42')
