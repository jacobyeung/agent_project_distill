"""Portable closures use the real component, mix, builder and native-reader gates."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from launch_r2 import build as B
from launch_r2.closure import transport
from student_pilot import r2_mix as M, r2_policy as P
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.r2_portable import bound
from tests.r2_init_fixture import INIT
from tests.test_r2_data_path import directory, LANE
from tests.test_r2_build import inputs
from tests.test_r2_policy import evidence


def fixture(root):
    registry=evidence(root/'e')
    mix=root/'mix.json'; write(mix,M.table())
    draws=M.allocation(M.table())
    cells={k:(v+3)//4 for k,v in draws.items()}
    cells['facing_pairs']+=(cells['facing_pairs']%2)
    pop=root/'population.json'
    write(pop,dict(schema='r2-filtered-population-v1', complete=True, exclusions=M.SEALED,
                   withheld_sha256=M.WITHHELD_SHA256,cells=cells,synthetic=True))
    counts=root/'counts.json'
    write(counts,dict(schema='r2-filtered-counts-v1',after_filtering=True,mix_sha256=file_pin(mix)['sha256'],
                      receipts=[file_pin(pop)],cells=cells,synthetic=True))
    groups={}; offsets={s:0 for s in M.table()['quotas']}
    for cell in M.table()['cells']:
        kind,stream=cell['type'],cell['stream']; start=offsets[stream]
        values=list(range(start,start+cells[kind])); offsets[stream]+=cells[kind]
        groups[kind]=[values[i:i+2] for i in range(0,len(values),2)] if kind=='facing_pairs' else values
    index=root/'index.json'
    write(index,dict(schema='r2-type-indices-v1',counts_sha256=file_pin(counts)['sha256'],cells=groups))
    return dict(mix=file_pin(mix),registry=registry,counts=file_pin(counts),indices=file_pin(index)), offsets


class Portable(unittest.TestCase):
    def test_complete_bindings_in_real_builder(self):
        root=directory(); bindings,counts=fixture(root)
        result=B.build(LANE/'work/kit07ca49df_meta/m',root/'a',connector='none',records=inputs(),bindings=bindings, init_pin=INIT_PIN)
        kit=root/'a'; config=load(kit/result['config']['path'])
        proof=P.preparation(config['r2_build2'],kit)
        self.assertTrue(all(x<=4 for x in proof['repeats'].values()))
        self.assertEqual(len(P.components(config['r2_build2']['registry'],'native_evaluation',kit)),14)
        self.assertEqual(B.verify(kit),result['kit_sha256'])
        previous=Path.cwd()
        try:
            os.chdir(kit)
            plan=next(M.plans(config['r2_sampling'],counts,1))
        finally:
            os.chdir(previous)
        self.assertEqual(sum(len(indices) for _,indices in plan),288)
        self.assertFalse(config['r2_build2']['admission'])
        mutation=deepcopy(config['r2_build2']); mutation['counts']={'path':'../outside','sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'escaped'):P.preparation(mutation,kit)
        changed=deepcopy(bindings); changed['indices']=bindings['indices']
        # Validate builder branches against the already staged source closure, without a second source copy.
        with patch.object(B,'tree_files',return_value={}):
            with self.assertRaisesRegex(ValueError,'indices require'):
                B.build(LANE/'work/kit07ca49df_meta/m',root/'b',connector='none',records=inputs(),
                        bindings={'registry':bindings['registry'],'indices':bindings['indices']}, init_pin=INIT_PIN)

    def test_closure_and_pin_refusals(self):
        root=directory(); bindings,_=fixture(root); target=root/'k';target.mkdir()
        def put(raw,suffix):
            identity=hashlib.sha256(raw).hexdigest();path=target/(identity+suffix);path.write_bytes(raw)
            return dict(path='k/'+path.name,sha256=identity)
        moved,registry=transport(bindings,put)
        self.assertEqual(P.preparation(moved,root)['draws'],M.allocation(M.table()))
        self.assertEqual(bound(bindings['mix']),Path(bindings['mix']['path']))
        marker=root/'marker.txt';marker.write_text('evidence')
        transport({'registry':file_pin(marker)},put)
        invalid=root/'asset.bin';invalid.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'metadata'):transport({'registry':file_pin(invalid)},put)
        with self.assertRaisesRegex(ValueError,'Unknown'):transport({'other':bindings['mix']},put)
        # Cycles cannot have genuine SHA256 pins. Force only the pin authentication boundary to reach that guard.
        cyclic=root/'cyclic.json';cyclic.write_text(json.dumps({'path':str(cyclic),'sha256':'c'*64}))
        with patch('launch_r2.closure.pinned',return_value=cyclic):
            with self.assertRaisesRegex(ValueError,'Cyclic'):transport({'registry':dict(path=str(cyclic),sha256='c'*64)},put)
        with self.assertRaisesRegex(ValueError,'escaped'):bound(dict(path='../outside',sha256='0'*64),root)

    def test_legacy_readers_refuse_before_loading_weights(self):
        from student_pilot import carrier_c1_run as run, grounding_eval
        pin={'path':'unused','sha256':INIT['artifact_sha256']}
        for cfg,artifact in [({},pin),({'geometry_connector':'none'},{'sha256':'f'*64}),
                             ({'init_artifact':{'artifact':pin}},{'sha256':'f'*64})]:
            with self.assertRaisesRegex(ValueError,'bank adapter'):run.inference(cfg,artifact,None)
            with self.assertRaisesRegex(ValueError,'bank adapter'):grounding_eval.load_runtime(cfg,artifact,None,None)
        P.legacy_reader_guard({'init_artifact':None},{'sha256':'f'*64})

from tests.r2_init_fixture import PIN as INIT_PIN
