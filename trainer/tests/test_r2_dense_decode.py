"""Real codec smoke for the evaluation frame-root path when PyAV is installed."""
import importlib.util
import unittest
from tests.test_r2_data_path import directory, fixture
from student_pilot.p3_provenance import file_pin
from student_pilot.dense_eval import decode_dense
import json
import os
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('av'), 'Frame-host decoder needs PyAV')
class Decode(unittest.TestCase):
    def test_real_video_and_mapped_sparse_frames(self):
        import av
        import numpy as np
        root = directory()
        row = fixture(root)
        movie = root/'clip.mp4'
        with av.open(str(movie), 'w') as container:
            stream = container.add_stream('mpeg4', rate=10)
            stream.width, stream.height, stream.pix_fmt = 32, 32, 'yuv420p'
            stream.codec_context.max_b_frames = 1
            for i in range(64):
                frame = av.VideoFrame.from_ndarray(np.full((32, 32, 3), i, dtype=np.uint8), format='rgb24')
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=json.dumps({'/logical/r2': str(root/'frames')})):
            dense = decode_dense(file_pin(movie), row['student_input'], {'dense_frames': 64}, root/'decoded')
        self.assertEqual(dense['frame_indices'], list(range(64)))
