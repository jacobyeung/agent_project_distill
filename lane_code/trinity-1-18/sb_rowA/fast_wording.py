"""Exact thresholded Levenshtein filter with Unicode code-point semantics."""
import ctypes,math
from pathlib import Path
from build_camera import normalized,THRESHOLD
_lib=ctypes.CDLL(str(Path(__file__).resolve().parent/'out/wording_distance.so'))
_dist=_lib.bounded_distance
_dist.argtypes=[ctypes.POINTER(ctypes.c_uint32),ctypes.c_int,ctypes.POINTER(ctypes.c_uint32),ctypes.c_int,ctypes.c_int]
_dist.restype=ctypes.c_int
_buffers={};_answers={}
def buffer(s):
 if s not in _buffers:_buffers[s]=(ctypes.c_uint32*len(s))(*map(ord,s))
 return _buffers[s]
def distance(a,b,cap):return _dist(buffer(a),len(a),buffer(b),len(b),cap)
def near(q,corpus):
 q=normalized(q);key=(id(corpus),q)
 if key in _answers:return _answers[key]
 for s in corpus:
  n=max(len(q),len(s));cap=math.ceil(THRESHOLD*n)-1
  if abs(len(q)-len(s))>cap:continue
  d=distance(q,s,cap)
  if d/n<THRESHOLD:
   _answers[key]={'normalized_reference':s,'distance':d/n};return _answers[key]
 _answers[key]=None;return None
