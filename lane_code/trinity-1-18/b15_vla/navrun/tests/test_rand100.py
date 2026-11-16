import copy
import hashlib
import unittest
from navrun.episodes import load_split
from navrun.io import read_json, write_json
from navrun.lists import load_rand100, freeze_rand100, verify_manifest
from navrun.paths import ROOT, RAND100


class Rand100Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.val=load_split('val_unseen')
        cls.data=read_json(RAND100)
        cls.path=ROOT/'out/tests/rand100/release.json.gz'

    def test_release_plain_json_order_and_identity(self):
        self.assertEqual(hashlib.sha256(RAND100.read_bytes()).hexdigest(),
                         'f4770f1baf87b936989e24c64ab10f69468676f485147ac528c7b8b9d639852f')
        eps=load_rand100(RAND100,self.val)
        self.assertEqual(len(eps),100)
        self.assertEqual(len({e.scene for e in eps}),10)
        self.assertEqual([e.episode_id for e in eps],[str(e['episode_id']) for e in self.data['episodes']])

    def test_freeze_roundtrip(self):
        target=ROOT/'out/tests/rand100/manifest.json'
        eps=freeze_rand100(RAND100,self.val,target)
        data=read_json(target)
        self.assertEqual(data['status'],'READY')
        self.assertEqual(eps,verify_manifest(data,self.val))

    def test_reject_mismatched_start(self):
        data=copy.deepcopy(self.data); data['episodes'][0]['start_position'][0]+=1
        write_json(self.path,data)
        with self.assertRaisesRegex(ValueError,'start position'): load_rand100(self.path,self.val)

    def test_reject_mismatched_scene_trajectory(self):
        for field in ('scene_id','trajectory_id'):
            data=copy.deepcopy(self.data); data['episodes'][0][field]='wrong'
            write_json(self.path,data)
            with self.assertRaisesRegex(ValueError,'mismatch'): load_rand100(self.path,self.val)

    def test_reject_duplicate_and_wrong_count(self):
        for records in (self.data['episodes'][:-1], self.data['episodes'][:-1]+[self.data['episodes'][0]]):
            write_json(self.path,dict(episodes=records))
            with self.assertRaises(ValueError): load_rand100(self.path,self.val)
