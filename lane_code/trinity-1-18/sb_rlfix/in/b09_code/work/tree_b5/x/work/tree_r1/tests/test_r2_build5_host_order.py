"""Run physical staging before packet resolution without admitting a full store."""
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tarfile
import unittest
from unittest.mock import patch

from tests.test_r2_data_path import directory
from student_pilot.p3_provenance import file_pin, load, write


def fixture():
    from launch_r2.host import POSE_SHA256
    root=directory();entries={}
    def entry(value):
        raw=json.dumps(value,sort_keys=True).encode();sha=hashlib.sha256(raw).hexdigest()
        name='u/'+sha
        entries[name]=dict(payload=base64.b64encode(raw).decode(),sha256=sha)
        return dict(path=name,sha256=sha)
    cfg=dict(input=entry(dict(value='fixture')))
    raw=b'{"archive_member":true}'
    sha=hashlib.sha256(raw).hexdigest();name='u/'+sha
    with tarfile.open(root/'source.tar','w') as archive:
        member=tarfile.TarInfo('member.json');member.size=len(raw)
        archive.addfile(member,io.BytesIO(raw))
    entries[name]=dict(archive=dict(parts=[str(root/'source.tar')],sha256=file_pin(root/'source.tar')['sha256']),
                       member='member.json',sha256=sha)
    cfg['archive_input']=dict(path=name,sha256=sha)
    write(root/'k/c.json',cfg)
    config=dict(path='k/c.json',sha256=file_pin(root/'k/c.json')['sha256'])
    poses=[entry(dict(source=name)) for name in ('one','two')]
    # Claim the required pins, but keep different tiny bytes. The real input
    # reader must reject those bytes after physical staging; no pose admission
    # predicate or local-node guard is substituted.
    poses=[{**pin,'sha256':sha} for pin,sha in zip(poses,sorted(POSE_SHA256))]
    packet=dict(manifests=[entry(dict(stream='vqa'))],pose_sources=poses,
                configuration=config,pose_template=entry(dict(kind='template')),
                real_proof=entry(dict(kind='proof')),counts=entry(dict(kind='counts')),
                output='o/result')
    launch=dict(config=dict(file=config['path'],sha256=config['sha256']))
    write(root/'k/launch.json',launch)
    executable=root/'venvs/rwtrain_torch211_cu129/bin/python'
    executable.parent.mkdir(parents=True);executable.write_bytes(b'fixture interpreter identity')
    (root/'b').mkdir();(root/'b/t.py').write_text('value = 1\n')
    write(root/'plan.json',dict(entries=entries,venv=dict(sha256='a'*64),bwrap=dict(sha256='b'*64)))
    write(root/'k/0.json',dict(staging=file_pin(root/'plan.json')))
    write(root/'o/01.json',dict(stdlib_version=[3,6],venv_sha256='a'*64,bwrap_sha256='b'*64,
                              files={'t.py':file_pin(root/'b/t.py')['sha256']}))
    return root,packet,cfg,entries,executable


class HostOrder(unittest.TestCase):
    def test_bootstrap_cli_refusal_is_opaque(self):
        from launch_r2 import staging
        output=io.StringIO()
        with patch.object(sys,'argv',['probe']),redirect_stdout(output):
            with self.assertRaises(SystemExit) as error:
                runpy.run_path(staging.__file__,run_name='__main__')
        self.assertEqual(error.exception.code,2)
        value=json.loads(output.getvalue())
        self.assertEqual(set(value),{'code','sha256'});self.assertEqual(value['code'],'E01')

    def test_full_host_stages_before_packet_byte_validation(self):
        from launch_r2 import host,staging
        root,packet,cfg,entries,executable=fixture()
        self.assertTrue(all(not (root/name).exists() for name in entries))
        write(root/'packet.json',packet)
        with patch.object(staging,'P',str(root)),patch.object(sys,'executable',str(executable)):
            with self.assertRaisesRegex(ValueError,'Input sha256 differs: pose_sources'):
                host.run_packet(root,file_pin(root/'packet.json'),full=True)
        for name,entry in entries.items():self.assertEqual(file_pin(root/name)['sha256'],entry['sha256'])
        for item in (1,2):self.assertEqual(load(root/'o/ee000008'/f'{item}.json')['status'],'PASS')
        self.assertFalse((root/'o/result').exists())
        proofs=Path(os.environ['R2_PROOFS'])
        (proofs/'HOST_ORDER.json').write_text(json.dumps(dict(
            staged_files=len(entries),checks={str(i):file_pin(root/'o/ee000008'/f'{i}.json') for i in (1,2)},
            final_refusal='Input sha256 differs: pose_sources',full_store_built=False,
            stand_in='runtime identity records and interpreter file bytes; real CPU allocation, physical staging and packet reader')))

    def test_physical_staging_failure_records_refusal(self):
        from launch_r2.checklist import Checklist
        root,packet,cfg,entries,executable=fixture()
        first=next(iter(entries));entries[first]['payload']=base64.b64encode(b'changed bytes').decode()
        plan=load(root/'plan.json');plan['entries']=entries
        (root/'plan.json').write_text(json.dumps(plan))
        (root/'k/0.json').write_text(json.dumps(dict(staging=file_pin(root/'plan.json'))))
        check=Checklist(root,packet,cfg)
        with self.assertRaisesRegex(ValueError,'Host check 2 refused'):check.step(2,check.stage_inputs)
        receipt=load(root/'o/ee000008/2.json')
        self.assertEqual(receipt['status'],'REFUSE');self.assertIn('reason_sha256',receipt)
        with self.assertRaisesRegex(ValueError,'incomplete'):check.finish()
        check.cfg={'input':'u/missing'}
        with self.assertRaisesRegex(ValueError,'Relative pins absent'):check.stage_inputs()

    def test_full_host_preflight_refusals(self):
        from launch_r2 import host
        root,packet,cfg,entries,executable=fixture()
        with self.assertRaisesRegex(ValueError,'Missing bound kit'):host.begin_checks(directory(),packet)
        launch=load(root/'k/launch.json')
        (root/'k/launch.json').write_text(json.dumps(dict(config={**launch['config'],'sha256':'0'*64})))
        with self.assertRaisesRegex(ValueError,'configuration differs'):host.begin_checks(root,packet)
        (root/'k/launch.json').write_text(json.dumps(launch))
        (root/'k/c.json').write_text(json.dumps({**cfg,'synthetic':True}))
        pin=file_pin(root/'k/c.json');packet['configuration']=pin
        (root/'k/launch.json').write_text(json.dumps(dict(config=dict(file=pin['path'],sha256=pin['sha256']))))
        with self.assertRaisesRegex(ValueError,'Synthetic inputs'):host.begin_checks(root,packet)
        root,packet,cfg,entries,executable=fixture()
        write(root/'proof.json',dict(synthetic=True));packet['real_proof']=file_pin(root/'proof.json')
        with self.assertRaisesRegex(ValueError,'Synthetic inputs'):host.begin_checks(root,packet)
        write(root/'plain.json',dict(value=True))
        packet['real_proof']=packet['counts']=file_pin(root/'plain.json')
        packet['pose_sources'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'sealed source pins'):host.begin_checks(root,packet)
