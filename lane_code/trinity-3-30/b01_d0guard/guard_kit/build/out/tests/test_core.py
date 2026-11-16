"""CPU logic tests; also runnable with system Python when the production env is absent."""
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import unittest
from unittest.mock import patch

B=Path(__file__).resolve().parents[2]
W=Path('/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/work')
ROOT=Path('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build/out/guard_kit/sj/orch_cd/evalx/work/milestone')
sys.path[:0]=[str(ROOT/'orchard_native'),str(ROOT/'native/out2'),str(ROOT)]
import native_metrics as M
import native_job as J
import kernels as K
import nomdg as N

# System Python is only a diagnostic fallback. Production runs use the native API.
if sys.version_info < (3, 8):
    import gzip, io
    def compress_compat(data, compresslevel=9, *, mtime=None):
        output=io.BytesIO()
        with gzip.GzipFile(fileobj=output,mode='wb',compresslevel=compresslevel,mtime=mtime) as stream:
            stream.write(data)
        return output.getvalue()
    gzip.compress=compress_compat

def load(p): return json.loads(Path(p).read_text())

def dev_tasks():
    archive=W/'obj/metadata_e10fbb95487f3baf.tar'
    names=('sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl',
           'sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl')
    result=[]
    with tarfile.open(str(archive)) as stream:
        for name in names:
            result.extend(json.loads(line) for line in stream.extractfile(name).read().decode().splitlines() if line)
    return {'devrows:'+row['id']:row for row in result if N.family(row['question_type']) in N.FAMILIES}

def report():
    value=load(W/'p9/native/probe/PILOT_REPORT.json')
    geom=value['geometry']
    refused=sorted(r['native'] for r in geom if r['status']=='REFUSED')
    value['gravity_guard_report']={'dev-S1':dict(captures=sorted(r['native'] for r in geom),
        capture_count=len(geom),sealed_refused=refused,sealed_refused_count=len(refused),
        reviewed_refused=refused,reviewed_refused_count=len(refused),
        reviewed_only_refused=[],reviewed_only_refused_count=0)}
    return value

class Core(unittest.TestCase):
    def test_p9_project(self):
        result=M.project(report())
        self.assertEqual(result['allocation_seconds'],21600)

    def test_program_refusal_project(self):
        r=report()
        row=next(x for x in r['items'] if not x.get('geometry_refusal'))
        row.update(finish='program_refusal',generated_tokens=0,decode_budget={},capped=False,
                   native_seconds=-1,seconds=-2)
        value=M.project(r)
        self.assertEqual(value['program_refusals']['total'],1)
        self.assertEqual(value['program_refusals']['per_family'][row['family']],1)
        self.assertEqual(sum(g['items'] for g in value['per_family'].values()),636)
        self.assertNotIn(row['key'],[b['key'] for b in value['item_time_bounds']])

    def test_program_refusal_sole_family_timing(self):
        r=report()
        row=next(x for x in r['items'] if x['family']=='camera_rotation')
        row.update(finish='program_refusal',generated_tokens=0,decode_budget={},capped=False)
        value=M.project(r,'none_capped')
        self.assertFalse(value['timing_measured'])
        self.assertFalse(value['fits'])

    def test_all_program_refusals(self):
        r=report()
        for row in r['items']:
            if not row.get('geometry_refusal'):
                row.update(finish='program_refusal',generated_tokens=0,decode_budget={},capped=False)
        value=M.project(r,'none_capped')
        self.assertEqual(value['program_refusals']['total'],9)
        self.assertFalse(value['timing_measured'])
        self.assertFalse(value['fits'])

    def test_program_refusal_terminal(self):
        r=report()
        row=next(x for x in r['items'] if not x.get('geometry_refusal'))
        row.update(finish='program_refusal',generated_tokens=0,decode_budget={},capped=False)
        dest=B/'work/test_terminal'
        out=dest/'native/probe'
        out.mkdir(parents=True,exist_ok=True)
        (out/'PILOT_REPORT.json').write_text(json.dumps(r))
        for name in ('GPU_PARITY.json','request.json','items.jsonl'):
            (out/name).write_text('{"pass":true}\n')
        geo=dest/'native/geometry'
        geo.mkdir(parents=True,exist_ok=True)
        (geo/'GEOMETRY_MANIFEST.json').write_text('{}\n')
        r['parity']={'path':str(out/'GPU_PARITY.json'),'sha256':M.C.sha(out/'GPU_PARITY.json')}
        (out/'PILOT_REPORT.json').write_text(json.dumps(r))
        cfg=load(W/'p9/metadata/CONFIG.json')
        def mapped(root,p):
            return dest if str(p)==cfg['logical_run'] else Path(p)
        with patch.object(J.S,'physical',side_effect=mapped):
            result=J.terminal(B,cfg)
        self.assertEqual(len(result),5)

    def test_pilot_report_counts(self):
        from types import SimpleNamespace
        cuda=SimpleNamespace(max_memory_allocated=lambda:0,max_memory_reserved=lambda:0)
        p=M.PilotReport(B/'work/test_report/PILOT_REPORT.json',load(W/'p9/metadata/CONFIG.json'),cuda)
        row=dict(family='camera_rotation',finish='program_refusal',capped=False)
        self.assertEqual(p.checkpoint('item',items=[row])['program_refusals']['total'],1)

    def test_selector_dev(self):
        tasks=dev_tasks()
        selected=N.parity_selection(tasks)
        expected=next(k for k in sorted(tasks) if tasks[k]['question_type']=='camera_displacement')
        self.assertEqual(selected['probe_key'],expected)
        self.assertEqual(len(selected['items']),5)
        (B/'out/SELECTOR_PROOF.json').write_text(json.dumps(dict(
            pilot9_probe=expected,c8_probe=selected['probe_key'],selection=selected,
            source=str(W/'obj/metadata_e10fbb95487f3baf.tar')),indent=2)+'\n')

    def test_selector_camera_free(self):
        tasks={key:row for key,row in dev_tasks().items()
               if not N.family(row['question_type']).startswith('camera_')}
        for key,row in tasks.items():
            self.assertEqual(key,'devrows:'+row['id'])
            self.assertTrue(all(name in row for name in ('native','question_type','question','options')))
        selected=N.parity_selection(tasks)
        self.assertEqual(len(tasks),186)
        self.assertEqual(selected['absent_families'],list(N.FAMILIES[:3]))
        self.assertEqual(selected['probe_key'],selected['items']['object_abs_distance'])
        (B/'out/tests/CAMERA_FREE_FIXTURE.json').write_text(json.dumps(dict(
            fixture=True,official_items_read=False,source=str(W/'obj/metadata_e10fbb95487f3baf.tar'),
            tasks={key:{name:row[name] for name in ('id','native','question_type','question','options')}
                   for key,row in tasks.items()},selection=selected),indent=2)+'\n')

    def test_selector_empty(self):
        with self.assertRaises(ValueError):N.parity_selection({})

    def test_pilot_zero_refusals(self):
        r=report()
        geom=[dict(x,status='PASS',error=None) for x in r['geometry']]
        selection=K.select_geometry_pilot(r['full_item_candidates'],r['registered_selection'],geom)
        self.assertEqual(selection['status'],'READY')
        self.assertEqual(len(selection['passed_item_keys']),10)
        self.assertEqual(selection['refused_item_keys'],[])

    def test_pilot_with_refusals(self):
        r=report()
        selection=K.select_geometry_pilot(r['full_item_candidates'],r['registered_selection'],r['geometry'])
        self.assertEqual(len(selection['passed_item_keys']),9)
        self.assertEqual(len(selection['refused_item_keys']),1)

    def test_guard_report(self):
        r=report()
        M.validate_gravity_guard(r['gravity_guard_report'],{'dev-S1':r['geometry']})
        r['gravity_guard_report']['dev-S1']['reviewed_only_refused']=['foreign']
        with self.assertRaises(ValueError):
            M.validate_gravity_guard(r['gravity_guard_report'],{'dev-S1':r['geometry']})

    def test_limit_source(self):
        source=(ROOT/'orchard_native/native_launcher.py').read_text()
        tree=ast.parse(source)
        values=[node for node in ast.walk(tree) if isinstance(node,ast.keyword) and node.arg=='gpu_seconds']
        self.assertEqual(len(values),1)
        code=compile(ast.Expression(values[0].value),str(ROOT/'orchard_native/native_launcher.py'),'eval')
        self.assertEqual(eval(code,{'mode':'pilot'}),6000)
        self.assertEqual(eval(code,{'mode':'full'}),21600)

    def test_pilot_scheduler_covers_limit(self):
        import native_launcher as launcher
        cfg=load(W/'p9/metadata/CONFIG.json')
        self.assertIn('--time=02:00:00',launcher.submit_argv(cfg))
        cfg['mode']='full'
        self.assertIn('--time=07:00:00',launcher.submit_argv(cfg))

if __name__=='__main__':unittest.main(verbosity=2)
