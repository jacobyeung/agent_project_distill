"""Synthetic masks use the real CachedSAM3 provider and C8r backend constructor."""
from types import SimpleNamespace as NS
import numpy as np
from .c8 import install
from .io import digest


def backend(geometry,audit_dir):
    P=install()
    from student_pilot.ground_sources import CachedSAM3
    kit,_=P.cache_tools()
    def rle(mask):
        flat=mask.flatten(order='F');values=[];last=False;n=0
        for bit in flat:
            if bit==last:n+=1
            else:values.append(n);last=bool(bit);n=1
        values.append(n)
        return {'size':list(mask.shape),'counts':values}
    cache={'phrases':['chair','table'],'frames':{}}
    for k in range(32):
        phrases={}
        for j,name in enumerate(cache['phrases']):
            mask=np.zeros((16,16),bool);mask[3:12,1+j*7:7+j*7]=True
            phrases[name]={'presence':.99,'prompt':name,'instances':[
                {'query':0,'score':.99,'joint_score':.9801,'box':[1+j*7,3,7+j*7,12], 'mask':rle(mask)}] if k==0 else []}
        cache['frames'][str(k)]={'size':[16,16],'phrases':phrases}
    source=CachedSAM3.__new__(CachedSAM3)
    source.cache=cache;source.reader=NS(phrase=kit.normalize_phrase,rle_decode=kit.decode)
    source.live=None;source.frame_indices=tuple(range(32));source.names=tuple(cache['phrases'])
    source.identity=digest(cache);source.provenance='synthetic_fixture_only'
    return P.backend({'question_type':'object_abs_distance'},
                     {'video_sha256':'f'*64,'frame_indices':list(range(32))},geometry,source,audit_dir)
