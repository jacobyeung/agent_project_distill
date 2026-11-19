"""Load CPU-only N row functions while refusing every torch operation."""
import sys,types
class _Inert(types.ModuleType):
 def __getattr__(self,name):
  if name.startswith('__'):raise AttributeError(name)
  return _Inert(self.__name__+'.'+name)
 def __call__(self,*a,**k):raise RuntimeError('Forbidden torch operation: '+self.__name__)
for name in ('torch','torch.nn','torch.nn.functional','torch.distributed','torch.utils','torch.utils.data'):
 sys.modules.setdefault(name,_Inert(name))
