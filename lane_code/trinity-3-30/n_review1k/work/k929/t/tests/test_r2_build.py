"""Empty-directory staging, stale closure, operational anonymity and metadata gates."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from launch_r2 import build as B
from student_pilot import r2_mix as M, r2_config as C
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.r2_materialize import materialize
from tests.test_r2_data_path import PROOFS, directory, LANE, fixture


def inputs():
    result=dict(withheld=LANE/'work/shared/WITHHELD_ROOMS_80.json',
                prereg=LANE/'work/records/design/REFREEZE_PREREGISTRATION_20261115.json',
                audit=LANE/'work/records/design/POLICY_AUDIT_20261115.md')
    from tests.test_r2_data_path import PROOFS, SOURCES, RECORDS
    result.update({k:RECORDS/v for k,v in SOURCES.items()})
    return result


def dense(root):
    path=root/'dense.json'
    write(path, dict(schema='r2-dense-manifest-v1', reconstruct_then_subsample=True,
                     synthetic=True, clips=[dict(id='synthetic', frames=list(range(64)))]))
    return file_pin(path)


class Build(unittest.TestCase):
    def test_two_empty_kits_and_mutations(self):
        root=directory(); dp=dense(root)
        base=LANE/'work/kit07ca49df_meta/m'
        results=[]
        for connector in ('none','gf1'):
            kit=root/('a0' if connector=='none' else 'a2')
            before=sum(p.stat().st_size for p in (LANE/'work/tmp').rglob('*') if p.is_file())
            result=B.build(base, kit, connector=connector, records=inputs(),dense_manifest=dp if connector=='gf1' else None, init_pin=INIT_PIN)
            after=sum(p.stat().st_size for p in (LANE/'work/tmp').rglob('*') if p.is_file())
            self.assertEqual(result['kit_sha256'],B.verify(kit))
            self.assertEqual(result['target_site'],C.SITE)
            result.update(tmp_before=before,tmp_after=after)
            results.append(result)
            config=kit/result['config']['path']; original=config.read_bytes()
            config.write_bytes(original+b' ')
            with self.assertRaises(ValueError): B.verify(kit)
            config.write_bytes(original)
            bad=kit/'k/other_SpLiT.json';bad.write_text('{}')
            with self.assertRaises(ValueError): B.scan(kit)
            bad.rename(kit/'k/abcdef.json')
            with self.assertRaises(ValueError): B.verify(kit)
            job=kit/'job.sh';job.write_text(job.read_text()+'export X=QWEN\n')
            with self.assertRaisesRegex(ValueError,'environment'):B.scan(kit)
            with self.assertRaises(ValueError): B.build(base,kit,connector=connector,records=inputs(),dense_manifest=dp, init_pin=INIT_PIN)
        (PROOFS/'B2_KIT_TESTS.json').write_text(json.dumps(results,indent=2)+'\n')

    def test_scanner_and_configuration_refusals(self):
        hashes=load(B.TREE/'launch_s1/b/wh.json')
        for key,value in [('path','k/revsi.json'),('env',{'X':'qwen'}),('env',{'X':'/scratch/node/abc'}),
                          ('args',['--SpLiT=dev']),('parts',['u/scannet']),('file','../abc')]:
            with self.assertRaises(ValueError): B.scan_value({key:value},hashes)
        self.assertFalse(B.bad_string('k/abcdef.json',hashes))
        self.assertTrue(B.bad_string('xxgeometryxx',hashes))
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        root=directory(); dp=dense(root)
        for connector in ('none','gf1'):
            with self.assertRaisesRegex(ValueError,'Camera'):
                C.configure({**parent,'camera_connector':True},connector,dense_manifest=dp, init_pin=INIT_PIN)
        with self.assertRaisesRegex(ValueError,'dense'): C.configure(parent,'gf1', init_pin=INIT_PIN)
        with self.assertRaises(ValueError): C.configure(parent,'other', init_pin=INIT_PIN)
        with self.assertRaises(ValueError): C.configure(parent,'none',stage=0, init_pin=INIT_PIN)
        with self.assertRaises(ValueError): C.configure({**parent,'geometry_online':{} or {'mode':'frozen'}},'none', init_pin=INIT_PIN)
        path=root/'invalid.json';write(path,{})
        with self.assertRaises(ValueError): C.configure(parent,'gf1',dense_manifest=file_pin(path), init_pin=INIT_PIN)
        cfg=C.configure(parent,'gf1',dense_manifest=dp, init_pin=INIT_PIN)
        with self.assertRaises(ValueError): C.apply_native(cfg)
        with self.assertRaises(ValueError): C.apply_native({**cfg,'camera_connector':True})

    def test_mix_metadata_before_materialization(self):
        root=directory()
        for fallback in (False,True):
            mix=M.table(fallback); mp=root/('fallback.json' if fallback else 'mix.json');write(mp,mix)
            totals=M.allocation(mix)
            self.assertEqual(sum(totals.values()),288000)
            self.assertEqual(totals['facing_pairs']%2,0)
            self.assertEqual({c['stream'] for c in mix['cells'] if c['type']=='route_planning'},{'vqa'})
            cp=root/('fc.json' if fallback else 'c.json')
            record=dict(schema='r2-filtered-counts-v1',after_filtering=True,mix_sha256=file_pin(mp)['sha256'],
                        receipts=[file_pin(mp)],cells={k:max(1,(n+3)//4) for k,n in totals.items()},synthetic=True)
            population=root/'population.json'
            def census(cells):
                population.write_text(json.dumps(dict(schema='r2-filtered-population-v1',complete=True,exclusions=M.SEALED,
                    withheld_sha256=M.WITHHELD_SHA256,cells=cells,synthetic=True)))
                return [file_pin(population)]
            record['receipts']=census(record['cells'])
            cp.write_text(json.dumps(record))
            source=root/'presence.json';source.write_text(json.dumps(dict(schema='r2-frame-host-presence-v1',second_pose_source='absent')))
            presence=file_pin(source) if fallback else None
            M.preflight(file_pin(mp),file_pin(cp),source_presence=presence)
            if fallback:
                with self.assertRaises(ValueError): M.preflight(file_pin(mp),file_pin(cp))
            for change in [dict(after_filtering=False),dict(receipts=[]),dict(cells={}),
                           dict(cells={**record['cells'],'pose':0}),dict(cells={**record['cells'],'pose':1})]:
                if 'cells' in change and change['cells']:
                    change['receipts']=census(change['cells'])
                cp.write_text(json.dumps({**record,**change}))
                with self.assertRaises(ValueError): M.preflight(file_pin(mp),file_pin(cp),source_presence=presence)
            with self.assertRaisesRegex(ValueError,'repeats'):
                materialize([],root/'never',mix_binding=dict(mix_pin=file_pin(mp),counts_pin=file_pin(cp),source_presence=presence))
            self.assertFalse((root/'never').exists())
        with self.assertRaises(ValueError): M.validate_table({**M.table(),'global_batch':1})
        row=fixture(root);row['question_type']='route_planning'
        self.assertEqual(M.check_route_rows([row],{'d1/fixture_clean'}),1)
        for rows,scenes in [([row,row],{'d1/fixture_clean'}),([row],set()),([{**row,'events':[{}]}],{'d1/fixture_clean'})]:
            with self.assertRaises(ValueError): M.check_route_rows(rows,scenes)

from tests.r2_init_fixture import PIN as INIT_PIN
