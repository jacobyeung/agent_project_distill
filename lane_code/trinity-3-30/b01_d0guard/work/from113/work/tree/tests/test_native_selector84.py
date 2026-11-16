"""All 84 dev scenes: arrays from public ground() equal hrp_infer exports."""
from collections import defaultdict
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import unittest
import numpy as np
import ofs
from ofs import core as O
from rk import sets
from rk.programs import load_heads
from rk.sam3mask import tower
from rk.report import make_report, read_jsonl
from student_pilot.geometry_profiles import legacy_from_heads
from student_pilot.scene_state import FrameMap, SceneState, digest
from student_pilot.ground_sources import CachedSAM3, file_sha256
from student_pilot.ground_v3 import GroundV3
from student_pilot.mdg_eval import read_npz
from student_pilot.p3_printed_calculator import PrintedPointRegistry

BASE=Path('/scratch/jjyeung/orch_cd')
ROOT=Path(os.environ.get('GV_FIX_ROOT',BASE/'gv_fix'))
E1=BASE/'ofs_e1/out/e1'


class NativeSelector84(unittest.TestCase):
    def test_all_84_default_backend_arrays(self):
        spec=importlib.util.spec_from_file_location('e1_runner',BASE/'ofs_e1/work/run_e1.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        grouped=defaultdict(list)
        for item in sets.dev_items():grouped[item['dataset']+'/'+item['scene']].append(item)
        index=json.loads((E1/'exports/A3_fwd/INDEX.json').read_text())
        self.assertEqual(len(index),84)
        reports=[];rows=[]
        for scene in sorted(index):
            stem=scene.replace('/','__');path=E1/'candidates'/f'{stem}.json'
            manifest=json.loads(path.read_text());mapping=FrameMap(tuple(manifest['frame_indices']))
            geo=legacy_from_heads(manifest['geometry'],mapping,load_heads)
            source=CachedSAM3(Path(manifest['raw']).parent,scene,mapping,tower(),path,names=manifest['names'])
            b=GroundV3(SceneState(digest(dict(scene=scene,frames=mapping.source_indices)),mapping,geo.identity),
                geo,source,mask_source='svp_sam3',selector=ofs,selector_identity=file_sha256(O.__file__),
                audit_dir=ROOT/'work/tmp/native84_audits')
            reference=BASE/'hrp_infer/out/oracle_dev/native_selected'/f'{stem}.npz'
            names,expected,_=read_npz(reference);actual=O.empty_values(len(names))
            for q,name in enumerate(names):
                b.ground(name,PrintedPointRegistry())
                slot=b.question_slots[name]
                self.assertIsNotNone(slot.values,(scene,name,slot.reason))
                for key in actual:actual[key][q]=slot.values[key][0]
            self.assertFalse(b.claims)
            differences={k:int(np.count_nonzero(actual[k]!=expected[k])) for k in expected}
            self.assertFalse(any(differences.values()),(scene,differences))
            grids=O.lift_grid(geo)
            rows.extend(runner.route(scene,grouped[scene],names,actual,geo,grids,{},.5))
            hashes={k:hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k,v in actual.items()}
            reports.append(dict(scene=scene,names=list(names),differences=differences,array_sha256=hashes,
                reference_sha256=file_sha256(reference),source_identity=source.identity,geometry_identity=geo.identity))
            print(json.dumps(dict(scene=scene,equal=True,names=len(names))),flush=True)
        direct=read_jsonl(BASE/'evalx/work/pulled5/dd_t0m800.jsonl')
        report=make_report(rows,direct,sets.answers('dev'))
        gains={t:round(v['delta']*100,2) for t,v in report['types'].items()}
        reviewer=json.loads((BASE/'gv_fix_review/out/SEL84.json').read_text())['gains_points']['hrp_native']
        self.assertEqual(gains,reviewer)
        result=dict(scenes=84,equal=84,profile='native_selector',entrypoint='GroundV3.ground',
                    verify='CPU P(yes)=1 stub',gains_points=gains,rows=len(rows),scene_reports=reports)
        (ROOT/'out/NATIVE_SELECTOR_84_R3.json').write_text(json.dumps(result,indent=1)+'\n')
        print(json.dumps(dict(scenes=84,equal=84,gains_points=gains)),flush=True)


if __name__=='__main__':unittest.main()
