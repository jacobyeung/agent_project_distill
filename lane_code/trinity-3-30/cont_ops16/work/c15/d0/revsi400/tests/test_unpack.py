import offline_guard
import copy
import io
import json
from pathlib import Path
import sys
import tarfile
import unittest
from unittest.mock import patch
import uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import unpack_result as U


class UnpackTests(unittest.TestCase):
    def test_authenticated_extraction_and_identity_refusal(self):
        p=ROOT/'evidence'/('unpack_'+uuid.uuid4().hex);(p/'fetched').mkdir(parents=True)
        cfg=dict(token='a1234567890',plan_sha256='a'*64);submission=dict(job=123)
        for name,value in [('CONFIG.json',cfg),('SUBMISSION.json',submission)]:
            (p/name).write_text(json.dumps(value))
        archive=p/'fetched/result.tar.gz'
        marker=json.dumps(dict(plan_sha256=cfg['plan_sha256'],synthetic=False)).encode()
        with tarfile.open(archive,'w:gz') as t:
            item=tarfile.TarInfo('COMPLETE.json');item.size=len(marker);t.addfile(item,io.BytesIO(marker))
        receipt=dict(token=cfg['token'],job=123,plan_sha256=cfg['plan_sha256'],schema='evalx-orchard-result-return-v1',
                     synthetic=False,status='COMPLETE',complete=True,conflicting_terminal_markers=False,returncode=0,
                     archive=dict(bytes=archive.stat().st_size,sha256=U.R.sha(archive)))
        (p/'fetched/EXIT.json').write_text(json.dumps(receipt))
        U.extract(p,p/'packet');self.assertEqual((p/'packet/COMPLETE.json').read_bytes(),marker)
        with self.assertRaises(FileExistsError):U.extract(p,p/'packet')
        for field,value in [('token','wrong'),('job',456)]:
            bad=dict(receipt,**{field:value});(p/'fetched/EXIT.json').write_text(json.dumps(bad))
            with self.assertRaises(ValueError):U.extract(p,p/'bad')
        bad=copy.deepcopy(receipt);bad['archive']['sha256']='0'*64;(p/'fetched/EXIT.json').write_text(json.dumps(bad))
        with self.assertRaises(ValueError):U.extract(p,p/'bad')
        self.assertFalse((p/'bad').exists())
