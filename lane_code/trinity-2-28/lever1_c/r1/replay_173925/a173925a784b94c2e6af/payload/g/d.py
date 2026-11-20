"""Versioned lossless transport with the requested float16 served-depth plane."""
import base64
import hashlib
import io
import json
from pathlib import Path
import zlib
import numpy as np

CAP = 1_000_000_000


def encode(geometry, metadata):
    depth = np.asarray(geometry.depth_grid, dtype='<f8')
    half = depth.astype('<f2')
    if not np.isfinite(half).all():
        raise ValueError('nonfinite or float16-overflow depth')
    residual = depth-half.astype('float64')
    if not np.array_equal(half.astype('float64')+residual, depth):
        raise ValueError('lossless residual failed')
    buf = io.BytesIO()
    np.savez_compressed(buf, depth=half, residual=residual, grid_uv=geometry.grid_uv)
    raw = buf.getvalue()
    return dict(schema=1, metadata=metadata, arrays=base64.b64encode(raw).decode(),
                arrays_sha256=hashlib.sha256(raw).hexdigest(),
                depth_sha256=hashlib.sha256(depth.tobytes()).hexdigest(),
                float16_max_error=float(np.max(np.abs(residual))),
                depth_units='metres', depth_scale_count=1)


def decode(row, *, half_only=False):
    if row['schema'] != 1 or row['depth_scale_count'] != 1:
        raise ValueError('depth schema/scale')
    raw = base64.b64decode(row['arrays'], validate=True)
    if hashlib.sha256(raw).hexdigest() != row['arrays_sha256']:
        raise ValueError('array digest')
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        half, residual, uv = z['depth'], z['residual'], z['grid_uv']
    if half.dtype != np.dtype('<f2') or half.shape != (32, 51, 51) or residual.shape != half.shape:
        raise ValueError('depth shape/type')
    exact = half.astype('float64')+residual
    if hashlib.sha256(exact.astype('<f8').tobytes()).hexdigest() != row['depth_sha256']:
        raise ValueError('depth digest')
    return half.astype('float64') if half_only else exact, uv


class Writer:
    def __init__(self, path, cap=CAP):
        self.stream=Path(path).open('xb'); self.codec=zlib.compressobj(6,zlib.DEFLATED,31)
        self.cap=cap; self.bytes=0; self.items=0
    def append(self, row):
        data=(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n').encode()
        import j
        data=j.pack(data)
        trial=self.codec.copy()
        chunk=trial.compress(data)+trial.flush(zlib.Z_SYNC_FLUSH)
        if self.bytes+len(chunk)+len(trial.copy().flush())>self.cap:
            raise ValueError('return cap')
        self.codec=trial; self.stream.write(chunk); self.stream.flush(); self.bytes+=len(chunk);self.items+=1
    def close(self):
        chunk=self.codec.flush();self.stream.write(chunk);self.bytes+=len(chunk);self.stream.close()
