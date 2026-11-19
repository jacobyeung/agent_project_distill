"""Local acceleration of exact normalized edit-distance filtering at 0.25."""
import ctypes, pathlib
class Filter:
 def __init__(self,refs):
  self.refs=refs
  u32=ctypes.c_uint32;ptr=ctypes.POINTER(u32)
  self.buffers=[(u32*len(s))(*map(ord,s)) for s in refs]
  self.ptrs=(ptr*len(refs))(*[ctypes.cast(b,ptr) for b in self.buffers])
  self.lens=(ctypes.c_int*len(refs))(*map(len,refs))
  self.lib=ctypes.CDLL(str(pathlib.Path(__file__).with_name('edit_filter.so')))
  self.fn=self.lib.first_near;self.fn.argtypes=[ptr,ctypes.c_int,ctypes.POINTER(ptr),ctypes.POINTER(ctypes.c_int),ctypes.c_int];self.fn.restype=ctypes.c_int
 def match(self,s):
  x=(ctypes.c_uint32*len(s))(*map(ord,s));r=self.fn(x,len(s),self.ptrs,self.lens,len(self.refs))
  if r==-2:raise MemoryError('edit-distance buffers')
  return r
