import ctypes, pathlib, math
from functools import lru_cache
lib=ctypes.CDLL(str(pathlib.Path(__file__).with_name('edit_distance.so')))
ptr=ctypes.POINTER(ctypes.c_uint32)
lib.bounded_distance.argtypes=[ptr,ctypes.c_int,ptr,ctypes.c_int,ctypes.c_int]
lib.bounded_distance.restype=ctypes.c_int
@lru_cache(maxsize=25000)
def encoded(s):return (ctypes.c_uint32*len(s))(*map(ord,s))
def distance(a,b,k):return lib.bounded_distance(encoded(a),len(a),encoded(b),len(b),k)
def nearest_rejected(q,refs,threshold):
 for ref in refs:
  n=max(len(q),len(ref),1);k=math.floor(threshold*n)
  if abs(len(q)-len(ref))>k:continue
  d=distance(q,ref,k)
  if d<=k:return ref,d/n
 return None
