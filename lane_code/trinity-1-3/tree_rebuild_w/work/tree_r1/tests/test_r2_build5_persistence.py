"""Exercise durable handoff with synthetic state bytes and transport boundaries."""
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from tests.test_r2_data_path import directory, LANE
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.r2_config import configure
from launch_r2 import persistence as P


def fixture():
    root = directory()
    cfg = configure(load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json'),'none', init_pin=INIT_PIN)
    cfg.update(output=str(root),r2_persistence={'synthetic':True})
    state = root/'s'
    state.mkdir()
    write(state/'artifact.json',dict(synthetic=True))
    (state/'w.bin').write_bytes(b'synthetic state boundary')
    return cfg, state


def records(path, key):
    raw = path.read_bytes()
    width = len(raw)//4
    return [dict(name=key+'.part'+str(i),generation=str(i+1),offset=i*width,
                 bytes=len(raw[i*width:(i+1)*width]),
                 sha256=hashlib.sha256(raw[i*width:(i+1)*width]).hexdigest()) for i in range(4)]


class Persistence(unittest.TestCase):
    def test_parent_writer_refuses_without_retry(self):
        from launch_s1.b import gcsput
        root=directory();path=root/'tiny.bin';path.write_bytes(b'fixture')
        calls=[]
        class Connection:
            def __init__(self,*args,**kwargs):calls.append(args)
            def putrequest(self,*args):pass
            def putheader(self,*args):pass
            def endheaders(self):pass
            def send(self,*args):pass
            def getresponse(self):return SimpleNamespace(status=503,read=lambda:b'unavailable')
        with patch('http.client.HTTPSConnection',Connection):
            with self.assertRaisesRegex(OSError,'HTTP 503'):
                gcsput.upload('https://invalid.invalid/session',path,0,path.stat().st_size,'j/fixture')
        self.assertEqual(len(calls),1)

    def test_native_state_inventory_and_changed_member(self):
        for corrupt in (False,True):
            cfg, unused=fixture()
            root=unused.parent
            bound=dict(synthetic=True)
            write(root/'binding.json',bound)
            state=root/'checkpoint_000001';(state/'shards').mkdir(parents=True)
            files={}
            for name in ('shards/rank000.pt','rng000.pt'):
                path=state/name;path.write_bytes(b'tiny synthetic bytes')
                files[name]={**file_pin(path),'bytes':path.stat().st_size}
            write(state/'complete.json',dict(schema='c1-checkpoint-v1',binding=bound,
                  layouts=[{}],step=1,files=files))
            if corrupt:
                (state/'rng000.pt').write_bytes(b'Tiny synthetic bytes')
                with self.assertRaisesRegex(ValueError,'member digest'):
                    P.upload(cfg,state,'checkpoint',records)
            else:self.assertTrue(P.upload(cfg,state,'checkpoint',records)['durable'])

    def test_plan_binding_and_native_state_refusals(self):
        cfg, state = fixture()
        with self.assertRaisesRegex(ValueError,'binding'):P.upload({},state,'export')
        with self.assertRaisesRegex(ValueError,'outside'):P.upload(cfg,directory(),'export')
        wrong={**cfg,'checkpoint_disk_guard':{**cfg['checkpoint_disk_guard'],'retained_archive_copies':0}}
        with self.assertRaisesRegex(ValueError,'disk guard'):P.plan(wrong)
        write(state.parent/'binding.json','fixture')
        write(state/'complete.json',dict(binding='fixture'))
        with self.assertRaisesRegex(ValueError,'predicate'):P.upload(cfg,state,'checkpoint',records)

    def test_archive_space_links_and_receipt_reuse(self):
        cfg,state=fixture()
        with patch.object(P.shutil,'disk_usage',return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError,'reserve'):P.upload(cfg,state,'export',records)
        cfg,state=fixture()
        (state/'s').symlink_to(state/'w.bin')
        with self.assertRaisesRegex(ValueError,'symlink'):P.upload(cfg,state,'export',records)
        cfg,state=fixture()
        first=P.upload(cfg,state,'export',records)
        self.assertEqual(first,P.upload(cfg,state,'export',records))

    def test_transport_receipt_refusals(self):
        cases={
            'generations':lambda r:r[:3],
            'ranges':lambda r:[{**r[0],'offset':1},*r[1:]],
            'exceeds':lambda r:[{**r[0],'bytes':100000},*r[1:]],
            'digest':lambda r:[{**r[0],'sha256':'0'*64},*r[1:]],
            'cover':lambda r:[{**x,'bytes':0,'offset':0,'sha256':hashlib.sha256(b'').hexdigest()} for x in r],
        }
        for reason,change in cases.items():
            with self.subTest(reason=reason):
                cfg,state=fixture()
                with self.assertRaisesRegex(ValueError,reason):
                    P.upload(cfg,state,'export',lambda p,k:change(records(p,k)))

    def test_milestone_collective_error_boundary(self):
        P.milestone({},None,None)
        cfg,state=fixture()
        cfg['r2_identity']={}
        with patch('torch.distributed.broadcast_object_list') as broadcast:
            P.milestone(cfg,state,'export',rank=1)
            broadcast.assert_called_once()
        cfg['r2_persistence']=None
        with self.assertRaisesRegex(ValueError,'Durable persistence refused'):
            P.milestone(cfg,state,'export',distributed=False)

    def test_pinned_transport_adapter(self):
        # This generated module is the transport byte boundary; archive construction,
        # module loading and receipt verification remain production functions.
        cfg,state=fixture()
        root=state.parent
        tool=root/'writer.py'
        tool.write_text('import hashlib,json\nfrom pathlib import Path\n'
            'def main(args):\n'
            ' raw=Path(args[3]).read_bytes(); width=len(raw)//4\n'
            ' rows=[dict(name=args[2]+".part"+str(i),generation=str(i+1),offset=i*width,bytes=width,sha256=hashlib.sha256(raw[i*width:(i+1)*width]).hexdigest()) for i in range(4)]\n'
            ' Path(args[1]+".receipts.jsonl").write_text("\\n".join(json.dumps(r) for r in rows))\n'
            ' return 0\n')
        write(root/'sessions.json',dict(synthetic=True))
        cfg['r2_persistence']=dict(sessions=file_pin(root/'sessions.json'),uploader=file_pin(tool))
        self.assertTrue(P.upload(cfg,state,'export')['durable'])
        cfg,state=fixture()
        tool=state.parent/'writer.py';tool.write_text('def main(args):\n return 1\n')
        write(state.parent/'sessions.json',{})
        cfg['r2_persistence']=dict(sessions=file_pin(state.parent/'sessions.json'),uploader=file_pin(tool))
        with self.assertRaisesRegex(ValueError,'upload failed'):P.upload(cfg,state,'export')

from tests.r2_init_fixture import PIN as INIT_PIN
