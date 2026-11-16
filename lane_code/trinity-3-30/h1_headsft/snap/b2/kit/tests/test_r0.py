import copy
import json
import sqlite3
import unittest
from pathlib import Path
from tests.fixtures import K
from student_pilot.h1_r0 import Reserve, room_key, prepare, before_admission
from student_pilot.p3_provenance import file_pin


class R0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.root=Path(tempfile.mkdtemp(prefix='r0_',dir=K/'tmp'))
        p=cls.root/'rooms.txt';p.write_text('scannet/scene0001\nscannetpp/abcdef1234\n');cls.pin=file_pin(p)
        cls.rows=[dict(dataset='scannet',scene='scene0001_00'),dict(dataset='ScanNetv2',scene='scene0001_09'),
                  dict(dataset='scannetppv2',scene='abcdef1234'),dict(dataset='scannet',scene='scene0002_01'),
                  dict(dataset='ARKitScenes',scene='abcdef1234')]
        db=cls.root/'rows.sqlite'
        with sqlite3.connect(db) as c:
            c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            c.executemany('INSERT INTO rows VALUES(?,?,?)',[(i,json.dumps(r),'{}') for i,r in enumerate(cls.rows)])
        cls.streams={name:dict(database=file_pin(db),count=5) for name in ('pose','vqa','routing','pointing')}
        cls.cfg=dict(h1=dict(r0_rooms=cls.pin),preparation_output=str(cls.root))

    def test_room_keys(self):
        self.assertEqual(room_key(dict(scene='scene0001_44')),'scannet/scene0001')
        self.assertEqual(room_key(dict(native='d2/abcdef1234')),'scannetpp/abcdef1234')
        self.assertEqual(room_key(dict(routing=dict(canonical='scannet/scene0001_02'))),'scannet/scene0001')
        rule=Reserve(self.pin)
        self.assertEqual([rule.excluded(r) for r in self.rows],[True,True,True,False,False])

    def test_preparation_and_admission_every_stream(self):
        receipt=dict(streams=self.streams)
        result=prepare(receipt,self.cfg)
        for name,s in result['streams'].items():
            self.assertEqual(s['count'],2)
            self.assertEqual(json.loads(Path(s['indices']['path']).read_text()),[3,4])
            self.assertEqual(result['h1_r0']['per_stream'][name],dict(seen=5,removed=3,retained=2))
        pre=before_admission(result,self.cfg)
        admitted=prepare(pre,self.cfg,phase='admission')
        self.assertEqual(admitted['streams'],result['streams'])
        self.assertEqual(admitted['h1_r0'],result['h1_r0'])
        # Admission also filters an unfiltered legacy receipt.
        self.assertEqual(prepare(before_admission(receipt,self.cfg),self.cfg,phase='admission')['streams'],result['streams'])

    def test_mismatch_and_tampering(self):
        with self.assertRaises(ValueError):Reserve({**self.pin,'sha256':'0'*64})
        result=prepare(dict(streams=self.streams),self.cfg)
        bad=copy.deepcopy(result);bad['streams']['pose']['count']=5
        with self.assertRaises(ValueError):before_admission(bad,self.cfg)
        with self.assertRaises(ValueError):before_admission(result,dict(h1={}))

    def test_off_identity(self):
        receipt=dict(streams=self.streams)
        before=json.dumps(receipt,sort_keys=True)
        self.assertIs(prepare(receipt,{}),receipt)
        self.assertIs(before_admission(receipt,{}),receipt)
        self.assertEqual(before,json.dumps(receipt,sort_keys=True))

    def test_pose_mix(self):
        order=self.root/'order.json';order.write_text(json.dumps([[0,i] for i in range(5)]))
        source=self.streams['pose']
        stream=dict(kind='mix',count=5,order=file_pin(order),sources=[dict(kind='rows',database=source['database'])])
        result=prepare(dict(streams={'pose':stream}),self.cfg)
        self.assertEqual(result['streams']['pose']['count'],2)
        self.assertEqual(result['h1_r0']['per_stream']['pose']['removed'],3)

if __name__=='__main__':unittest.main()
