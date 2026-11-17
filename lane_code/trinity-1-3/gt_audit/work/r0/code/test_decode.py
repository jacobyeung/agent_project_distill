"""Decode determinism and layout test on a synthetic 1920x1440 60 fps H.264 video (PyAV encoder)."""
import json, os, sys, time, unittest
import av, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import decode_frames, r0lib  # noqa: E402
D = os.path.join(os.path.dirname(HERE), 'work', 'test_decode', 'run_%d_%d' % (int(time.time()), os.getpid()))


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(D + '/scene/iphone')
        n = 150
        json.dump({'frame_%06d' % i: {} for i in range(n)}, open(D + '/scene/iphone/pose_intrinsic_imu.json', 'w'))
        with av.open(D + '/scene/iphone/rgb.mkv', 'w') as c:
            s = c.add_stream('libx264', rate=60); s.width, s.height, s.pix_fmt = 1920, 1440, 'yuv420p'
            for i in range(n):
                img = np.zeros((1440, 1920, 3), np.uint8); img[:, :, 0] = i; img[100:300, 10 * i % 1800:10 * i % 1800 + 100] = 255
                for p in s.encode(av.VideoFrame.from_ndarray(img, format='rgb24')):
                    c.mux(p)
            for p in s.encode():
                c.mux(p)
        cls.r1 = decode_frames.main(D + '/scene', D + '/f1', D + '/m1.json')
        cls.r2 = decode_frames.main(D + '/scene', D + '/f2', D + '/m2.json')

    def test_count_and_layout(self):
        self.assertTrue(self.r1['count_match']); self.assertEqual(self.r1['missing'], [])
        self.assertEqual(sorted(map(int, self.r1['frames'])), sorted(set(r0lib.layout(150, 32) + r0lib.layout(150, 64))))

    def test_deterministic(self):
        self.assertEqual(self.r1['frames'], self.r2['frames'])

    def test_frame_identity(self):
        from PIL import Image
        for i in (0, 149):
            a = np.asarray(Image.open(D + '/f1/%06d.png' % i)); self.assertEqual(a.shape, (480, 640, 3))
            self.assertLess(abs(int(np.median(a[400:, :, 0])) - i), 6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
