"""Keep the registered scorer tests and exercise diagnostic decode validation."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent.parent/'cap/score_tower2x_b'
sys.path.insert(0, str(OLD))
spec = importlib.util.spec_from_file_location('score', ROOT/'score.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
sys.modules['score'] = S
import test_score
import test_k3c
spec = importlib.util.spec_from_file_location('worker', ROOT/'2.py')
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)
test_score.W = W


def inputs():
    data, ref = test_k3c.inputs()
    ref['decode_recording'] = True
    for row in data['rows']:
        for arm in row['arms']:
            arm.update(raw_matches=[True]*len(arm['ids']), raw_match_count=len(arm['ids']),
                       decode_versions=[dict(cv2='4.10.0',PIL='11.1.0',numpy='1.26.4') for _ in arm['ids']])
    data.update(raw_match_count=950,raw_frame_count=950)
    return data, ref


class K3d(unittest.TestCase):
    def test_drift_does_not_change_camera_verdict(self):
        data, ref = inputs()
        before = S.score(data,ref)
        for row in data['rows']:
            for arm in row['arms']:
                arm['raw_sha256'] = ['f'*64]*len(arm['ids'])
                arm['raw_matches'] = [False]*len(arm['ids'])
                arm['raw_match_count'] = 0
        data['raw_match_count'] = 0
        after = S.score(data,ref)
        self.assertEqual(before['decisions'],after['decisions'])
        self.assertEqual(before['decode_control'],after['decode_control'])
        self.assertEqual(after['verdict'],'confirm')
        for a,b in zip(before['rows'],after['rows']):
            for label in ("A'",'B'):
                for key in ('rigid','similarity','relative','gravity'):
                    self.assertEqual(a['arms'][label][key],b['arms'][label][key])

    def test_forged_decode_records_rejected(self):
        mutations = [lambda a:a['raw_matches'].__setitem__(0,False),
                     lambda a:a.__setitem__('raw_match_count',31),
                     lambda a:a['raw_sha256'].__setitem__(0,'bad'),
                     lambda a:a.__setitem__('decode_versions',[]),
                     lambda a:a['decode_versions'][0].__setitem__('cv2','')]
        for mutate in mutations:
            data,ref=inputs()
            mutate(data['rows'][0]['arms'][0])
            with self.assertRaises(ValueError):S.score(data,ref)

    def test_png_binding_stays_fatal(self):
        for key in ('ids','sha256','slots'):
            data,ref=inputs()
            data['rows'][0]['arms'][0][key] = list(reversed(data['rows'][0]['arms'][0][key]))
            with self.assertRaises(ValueError):S.score(data,ref)

    def test_totals_rejected(self):
        for key in ('raw_match_count','raw_frame_count'):
            data,ref=inputs()
            data[key]-=1
            with self.assertRaises(ValueError):S.score(data,ref)

    def test_incomplete_decode_records_do_not_change_control(self):
        data,ref=inputs()
        test_k3c.alter_controls(ref,3)
        self.assertEqual(S.score(data,ref)['verdict'],'void')


if __name__ == '__main__':
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)
                             for m in (test_score,test_k3c,sys.modules[__name__]))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
