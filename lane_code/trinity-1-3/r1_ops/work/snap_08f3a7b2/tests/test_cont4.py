"""Replay the generated audit with the sealed trainer and prepared CPU fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tarfile
import unittest

from rebind import ROOT, load, sha, write, pin
from test_fix11 import Fix11


def prepared_fixture(root, x, trainer, *, bad_routing=False):
    # The full immutable trainer archive is local and contains regular files only.
    with tarfile.open(ROOT/'out/r1p_code.tar') as archive:
        for member in archive:
            path = trainer/member.name
            if Path(member.name).is_absolute() or '..' in Path(member.name).parts:
                raise ValueError('Unsafe trainer fixture member')
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True, mode=0o700)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                path.write_bytes(archive.extractfile(member).read())
            else:
                raise ValueError('Nonregular trainer fixture member')
    kit = Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])
    (x/'b/d.py').write_bytes((kit/'b/d.py').read_bytes())
    (x/'b/i.py').write_bytes((kit/'b/i.py').read_bytes())
    # d.config_identity imports i, whose top-level verifier imports remain real.
    for path in (kit/'b').glob('*.py'):
        (x/'b'/path.name).write_bytes(path.read_bytes())
    sys.path.insert(0, str(ROOT/'work/tree'))
    from student_pilot import type_mix
    from student_pilot.carrier_c1_run import identity
    from student_pilot.p3_provenance import digest
    from student_pilot.vehicle_p import ROUTING
    cfg = load(ROOT/'out/config.json')
    key = load(ROOT/'out/BINDING.json')['run_key']
    output = x/'runs'/key
    inputs = output/'inputs'
    inputs.mkdir(parents=True, mode=0o700)
    cfg['output'] = str(output)
    cfg['recipe'].update(steps=1, mix=['vqa']+['routing']*4)
    cfg['type_mix'] = dict(schema='type-mix-v2', max_repeats=4, size_selector=None,
        streams=dict(vqa=dict(cells=dict(totals={'cents':400},room={'cents':0},size={'cents':0}),refill=['totals']),
                     routing=dict(cells={name:{'cents':400} for name in ROUTING},refill=list(ROUTING))))
    write(inputs/'selection.json', dict(sources={}))
    cfg['s1_routing']['selection'] = pin(inputs/'selection.json')
    write(x/'k/config.json', cfg)
    derived = copy.deepcopy(cfg)
    derived.pop('admission', None)
    derived['preparation_output'] = str(inputs)
    scenes = dict(coverage=dict(schema='s1-scene-coverage-result-v1',status='PASS',
        policy=cfg['scene_coverage'],sources={'fixture':{'status':'PASS'}}))
    sources = {}
    for stream in ('vqa','routing'):
        db = inputs/(stream+'.sqlite')
        conn = sqlite3.connect(db)
        conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        names = ['object_counting'] if stream=='vqa' else list(ROUTING[:3])+['absolute_distance_object']
        rows = []
        for name in names:
            for _ in range(10):
                row = dict(qid='fixture_'+str(len(rows)),question_type=name,target='2',
                    count_kind='total',provenance={'canonical':'unknown/scene' if bad_routing else 'scannet/scene'})
                rows.append(row)
        conn.executemany('INSERT INTO rows VALUES(?,?,?)',
            [(i,json.dumps(row),json.dumps(row['target'])) for i,row in enumerate(rows)])
        conn.commit();conn.close()
        sources[stream] = dict(database=pin(db),count=len(rows))
    write(inputs/'v.json', dict(schema='c1-stream-v1',stream='vqa',
        source=cfg['streams']['vqa'],source_receipt=cfg['streams']['vqa']))
    derived['streams']['vqa'] = pin(inputs/'v.json')
    write(inputs/'pointing.json', {'fixture':True})
    derived['streams']['pointing'] = pin(inputs/'pointing.json')
    write(inputs/'materialization.json', dict(schema='s1-routing-materialization-v1',status='PASS',
        inputs=cfg['s1_routing'],legacy=cfg['streams']['routing']))
    materialization = pin(inputs/'materialization.json')
    write(inputs/'routing.json',dict(materialization=materialization))
    derived['streams']['routing'] = pin(inputs/'routing.json')
    code = load(ROOT/'out/records/c.json')
    sealed = dict(schema='s1-run-seal-v1',tree_sha256=code['tree_sha256'],
        config_sha256=identity(derived),archive=code['archive'])
    seal = dict(sealed,sha256=digest(sealed))
    receipt = type_mix.prepare(dict(config_sha256=identity(derived),streams=sources,
        scene_filter_report=scenes,source_seal=seal,stream_status={'mdg':'absent'}),derived)
    write(inputs/'prepared.json',receipt)
    derived['preparation'] = pin(inputs/'prepared.json')
    write(inputs/'effective.json',derived)
    write(inputs/'frames.json',dict(all_retained_frames_exist=True,sources={'fixture':True}))
    write(inputs/'parent.json',dict(schema='s1-parent-grounding-v1',status='PASS',
        parent_artifact=cfg['init_artifact']['artifact'],mdg='absent',
        method='verify-parent-metadata-without-mdg',parent_base_identity=cfg['base_identity'],
        parent_weight_payloads_verified=False,full_parent_model_loaded=False))
    write(inputs/'data_receipt.json',dict(schema='s1-in-job-data-v1',status='PREPARED',
        production_authorized=False,rehearsal=False,real_frames_verified=True,gpu_first_step_pending=True,
        source_revision=code['commit'],input_config=pin(x/'k/config.json'),world_size=cfg['world_size'],
        input_streams=cfg['streams'],config=pin(inputs/'effective.json'),preparation=derived['preparation'],
        routing_materialization=materialization,scene_exclusions=scenes,source_seal=seal,
        source_counts={s:v['count'] for s,v in sources.items()},frames=pin(inputs/'frames.json'),
        parent_grounding=pin(inputs/'parent.json'),mdg='absent'))
    write(x/'k/launch.json',dict(config={'file':'k/config.json',**pin(x/'k/config.json')},
        source_revision=code['commit'],source_seal={'tree_sha256':code['tree_sha256'],'archive':code['archive']},
        run_directory=str(output),in_job_admission=dict(schema='s1-in-job-admission-v1',directory=str(inputs),
            parent_grounding_required=True,gpu_first_step_required=True,frame_roots=[str(inputs)])))


class ZPostAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fix11.setUpClass()

    def test_real_loader_main_and_receipt_writes(self):
        replay = Fix11()
        root,outcome = replay.fixture(prepare=prepared_fixture,namespace=True)
        self.assertEqual(outcome['rc'],0,(root/'shell.log').read_text())
        report = outcome['loader_fixture']
        self.assertEqual(report['status'],'PASS')
        self.assertTrue(all(v['status']=='PASS' for v in report['checks'].values()))
        env = load(root/'environment.json')
        self.assertNotIn(env['TRAINER'],env['PYTHONPATH'].split(':'))
        x = root/'mount'; key = load(ROOT/'out/BINDING.json')['run_key']
        inputs = x/'runs'/key/'inputs'
        self.assertEqual(report['checks']['loader_audit']['pin'],pin(inputs/'l.json'))
        self.assertIn(['--bind',env['TK_RUNS_DIR'],str(x/'runs')],load(root/'mounts.json'))
        self.assertFalse((x/'b/student_pilot').exists())
        from student_pilot.carrier_c1_run import identity
        self.assertEqual(report['original_config_identity'],identity(load(x/'k/config.json')))
        self.assertEqual(report['effective_config_identity'],identity(load(inputs/'effective.json')))
        self.assertFalse(list(Path(env['TRAINER']).rglob('*.pyc')))
        write(ROOT/'out/proof/CONT4_LOADER_REPLAY.json',dict(status='PASS',fixture=str(root),
            proof_sha256=sha(ROOT/'out/proof/p.py'),audit=pin(inputs/'a.json'),loader=pin(inputs/'l.json'),
            trainer=env['TRAINER'],pythonpath=env['PYTHONPATH'],checks=report['checks'],
            scope='Real generated heredoc, v.tree, sealed trainer, d.effective, loader audit, bwrap namespace and report writes; synthetic prepared rows; no production admission.'))

    def test_real_loader_failure_propagates(self):
        root,outcome = Fix11().fixture(prepare=lambda *args:prepared_fixture(*args,bad_routing=True),namespace=True)
        self.assertNotEqual(outcome['rc'],0)
        self.assertEqual(outcome['status'],'FAIL')
        key = load(ROOT/'out/BINDING.json')['run_key']
        report = load(root/'mount/runs'/key/'inputs/a.json')
        self.assertEqual(report['checks']['loader_audit']['status'],'FAIL')
        self.assertIn('Required packet proof checks failed',(root/'shell.log').read_text())

    def test_rehearsal_real_loader_reaches_missing_admission(self):
        def setup(root,x,trainer):
            prepared_fixture(root,x,trainer)
            cfg=load(x/'k/config.json');output=Path(cfg['output']);inputs=output/'inputs'
            (inputs/'data_receipt.json').rename(inputs/'withheld_receipt.json')
            write(inputs/'staged_vqa.json',dict(database=pin(inputs/'vqa.sqlite')))
            cfg['streams']['vqa']=pin(inputs/'staged_vqa.json');write(x/'k/config.json',cfg)
        root,outcome=Fix11().fixture(prepare=setup,namespace=True,rehearsal=True)
        self.assertEqual(outcome['rc'],0,(root/'shell.log').read_text())
        receipt=outcome['loader_fixture']
        self.assertEqual(receipt['status'],'REHEARSAL_OK')
        self.assertFalse(receipt['admission_executed'])
        self.assertEqual(receipt['steps']['admission_output_boundary'],'EXPECTED_MISSING')
        self.assertNotIn('stub admission rc=0',(root/'shell.log').read_text())
        write(ROOT/'out/proof/CONT4_REHEARSAL.json',dict(status='PASS',fixture=str(root),
            receipt=receipt,proof_sha256=sha(ROOT/'out/proof/p.py'),
            scope='Exact generated rehearsal tail and native loader inside local bwrap; synthetic staged SQLite store.'))

    def test_rehearsal_failure_receipts_cannot_pass(self):
        import tempfile
        for rc in (0,7):
            root=Path(tempfile.mkdtemp(prefix='tail_failure_',dir=ROOT/'work'))
            kh=root/'kit';(kh/'o').mkdir(parents=True,mode=0o700)
            script="printf 'REHEARSAL_STEP bwrap_setup PASS\\nREHEARSAL_STEP environment PASS\\nREHEARSAL_STEP pythonpath PASS\\n'\nexit "+str(rc)+"\n"
            result=Fix11.proof.rehearsal_execute(['/bin/bash','-s'],script,kh,root,'12345',Fix11.key)
            self.assertEqual(result['status'],'REHEARSAL_FAIL')
            self.assertEqual(result['rc'],rc or 1)
            self.assertEqual(result['steps']['namespace'],'FAIL')
            self.assertEqual(result['steps']['trainer_tree'],'NOT_RUN')
            self.assertFalse(result['admission_executed'])
            self.assertFalse((kh/'o/12345.proof.json').exists())

    def test_rehearsal_generator_excludes_admission_and_has_distinct_receipts(self):
        p=Fix11.proof;k=Fix11.kit
        text=p.rehearsal_program((ROOT/'out/operator/jb.sh').read_text(),(k/'job.sh').read_text(),k,'/usr/bin/bwrap')
        self.assertNotIn('/bin/bash "$ROOT/b/r.sh" p 0',text)
        self.assertNotIn('tk_stage',text)
        self.assertLess(text.index('tk_nx'),text.index('tk_bwrap'))
        self.assertLess(text.index('tk_env'),text.index('tk_pythonpath p'))
        self.assertLess(text.index('tree({'),text.index('from student_pilot.loader_audit'))
        source=(ROOT/'out/proof/p.py').read_text()
        self.assertIn("'.rehearsal.json' if rehearsal_root else '.proof.json'",source)
        self.assertIn("result['status']!='REHEARSAL_OK'",source)


if __name__=='__main__':unittest.main(verbosity=2)
