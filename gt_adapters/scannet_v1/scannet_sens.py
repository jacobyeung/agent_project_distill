"""Bounded reader for released, calibrated ScanNet SensorData v4 streams."""
from __future__ import annotations
import hashlib
import struct
import zlib
from pathlib import Path
import cv2
import numpy as np


def rigid(matrix, name):
    value = np.asarray(matrix, dtype=np.float64)
    if (value.shape != (4, 4) or not np.isfinite(value).all()
            or not np.allclose(value[3], [0, 0, 0, 1], atol=1e-5)
            or not np.allclose(value[:3, :3].T @ value[:3, :3], np.eye(3), atol=1e-4)
            or not np.isclose(np.linalg.det(value[:3, :3]), 1, atol=1e-4)):
        raise ValueError(f'{name} must be a finite proper rigid transform')
    return value


class SensReader:
    """Index frame records without retaining the multi-GB compressed stream in memory."""
    def __init__(self, path):
        self.path = Path(path)
        self.size = self.path.stat().st_size
        with self.path.open('rb') as f:
            def read(fmt):
                n = struct.calcsize('<' + fmt)
                data = f.read(n)
                if len(data) != n:
                    raise ValueError('truncated .sens field')
                return struct.unpack('<' + fmt, data)

            version, = read('I')
            if version != 4:
                raise ValueError('only official .sens version 4 is supported')
            length, = read('Q')
            if length > 4096 or f.tell() + length > self.size:
                raise ValueError('invalid .sens sensor name length')
            name = f.read(length).decode('utf-8')
            self.header = dict(version=version, sensor_name=name)
            for field in ('intrinsic_color', 'extrinsic_color', 'intrinsic_depth', 'extrinsic_depth'):
                self.header[field] = np.asarray(read('16f')).reshape(4, 4).tolist()
            color, depth, cw, ch, dw, dh, shift, count = read('2i4IfQ')
            if color != 2 or depth != 1:
                raise ValueError('supported .sens codecs are JPEG color and zlib ushort depth')
            if min(cw, ch, dw, dh) <= 0 or max(cw, ch, dw, dh) > 16384 or not np.isfinite(shift) or shift <= 0:
                raise ValueError('invalid .sens raster or depth shift')
            if count < 1 or count > (self.size - f.tell()) // 96:
                raise ValueError('invalid .sens frame count')
            self.header.update(color_compression=color, depth_compression=depth,
                               color_wh=[cw, ch], depth_wh=[dw, dh], depth_shift=shift,
                               num_frames=count)
            self.records = []
            for ordinal in range(count):
                start = f.tell()
                pose = np.asarray(read('16f')).reshape(4, 4).tolist()
                tc, td, nc, nd = read('4Q')
                offset = f.tell()
                if min(nc, nd) <= 0 or offset + nc + nd > self.size:
                    raise ValueError('truncated .sens compressed frame payload')
                self.records.append(dict(source_frame_id=ordinal, record_offset=start,
                    camera_to_world=pose, timestamp_color_us=tc, timestamp_depth_us=td,
                    color_offset=offset, color_size=nc, depth_offset=offset + nc, depth_size=nd))
                f.seek(nc + nd, 1)
            # SensorData v4 may append an IMU count and 15 doubles + timestamp per sample.
            remaining = self.size - f.tell()
            imu = 0
            if remaining:
                imu, = read('Q')
                if self.size - f.tell() != imu * 128:
                    raise ValueError('invalid .sens trailing IMU records')
            self.header['num_imu_records'] = imu

    def decode(self, ordinal):
        if type(ordinal) is not int or not 0 <= ordinal < len(self.records):
            raise ValueError('source frame ordinal outside .sens stream')
        row = dict(self.records[ordinal])
        with self.path.open('rb') as f:
            f.seek(row['color_offset'])
            color_bytes = f.read(row['color_size'])
            depth_bytes = f.read(row['depth_size'])
        if len(color_bytes) != row['color_size'] or len(depth_bytes) != row['depth_size']:
            raise ValueError('truncated selected .sens payload')
        color = cv2.imdecode(np.frombuffer(color_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        cw, ch = self.header['color_wh']
        dw, dh = self.header['depth_wh']
        if color is None or color.shape != (ch, cw, 3):
            raise ValueError('decoded .sens color canvas differs from header')
        decoder = zlib.decompressobj()
        raw = decoder.decompress(depth_bytes, dw * dh * 2 + 1)
        if len(raw) != dw * dh * 2 or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('invalid .sens depth payload size or zlib stream')
        depth = np.frombuffer(raw, dtype='<u2').reshape(dh, dw).copy()
        row.update(color_payload_sha256=hashlib.sha256(color_bytes).hexdigest(),
                   depth_payload_sha256=hashlib.sha256(depth_bytes).hexdigest(),
                   depth_nonzero_pixels=int(np.count_nonzero(depth)))
        return color, depth, row


def calibrated_header(header):
    """Identity extrinsics identify already color-aligned released sensor streams."""
    for field in ('extrinsic_color', 'extrinsic_depth'):
        matrix = rigid(header[field], field)
        if not np.array_equal(matrix, np.eye(4)):
            raise ValueError('nonidentity sensor extrinsic requires a separately reviewed adapter')
    for field in ('intrinsic_color', 'intrinsic_depth'):
        matrix = np.asarray(header[field])
        if (matrix.shape != (4, 4) or not np.isfinite(matrix).all()
                or not np.array_equal(matrix[2:], np.eye(4)[2:])
                or not np.array_equal(matrix[:2, 3], [0, 0])
                or not np.array_equal([matrix[0, 1], matrix[1, 0]], [0, 0])
                or min(matrix[0, 0], matrix[1, 1]) <= 0):
            raise ValueError('invalid official zero-skew intrinsic')
    return np.asarray(header['intrinsic_color'], dtype=np.float64)[:3, :3]
