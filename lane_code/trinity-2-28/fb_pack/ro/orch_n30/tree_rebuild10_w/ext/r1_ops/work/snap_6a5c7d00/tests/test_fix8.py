"""Proof-2 regressions on the pinned slice and printed proof boundaries."""
import contextlib,copy,hashlib,importlib.util,io,json,os,subprocess,sys,tarfile,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7'),str(ROOT/'tools')]
from rebind import load,sha,write
SLICE=Path('/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl')
SLICE_SHA='5f9383fa3dabcc813676564c8533e0c7b110a7f1d0e9aff4c9ebde444355a0b3'

def temp():return Path(tempfile.mkdtemp(prefix='fix8_',dir=ROOT/'work'))

class Fix8(unittest.TestCase):
    def test_real_packing_payload_pins_and_native_selection(self):
        from unit_binding import pack_slice,regenerate
        from student_pilot import s1_routing,s1_pool
        from student_pilot.vehicle_p import unit_name,ROUTING
        from selection_check import project
        root=temp();binding=load(ROOT/'out/BINDING.json');cfg=load(ROOT/'out/config.json')
        authority=load(ROOT/'out/FRAME_AUTHORITY.local.json')
        parent,_=project(load(ROOT/'work/records/pool_selection_eac5f9f0.json'))
        parent['implementation']=s1_pool.implementation()
        frames=s1_routing.Frames(authority['frame_map'],authority['frame_plan'],fps_authority=authority['fps_authority'])
        with patch.object(s1_routing,'Frames',return_value=frames):
            packed=pack_slice(SLICE,SLICE_SHA,authority,cfg['s1_routing'],parent,root/'packed.jsonl')
        self.assertEqual(packed['input_rows'],747);self.assertEqual(packed['rows'],747)
        self.assertEqual(packed['sealed_validation_pass'],747);self.assertEqual(packed['refusals'],[])
        self.assertEqual(packed['refused_rows'],0)
        self.assertEqual(sha(root/'packed.jsonl'),binding['unit_binding']['input_sha256'])
        original=[json.loads(line) for line in SLICE.read_text().splitlines()]
        result=[json.loads(line) for line in (root/'packed.jsonl').read_text().splitlines()]
        counts=Counter()
        for before,after in zip(original,result,strict=True):
            for key,value in before.items():self.assertEqual(after[key],value)
            self.assertEqual(set(after)-set(before),{'events','student_input'})
            s1_pool.validate_source_row(after,'packed');counts[unit_name(after)]+=1
            request=s1_routing.frame_request(after)
            self.assertEqual(after['student_input']['frames'],[frames.frames[request['d'],request['s'],i] for i in request['i']])
        self.assertEqual(dict(counts),{'ft':683,'in':64});self.assertEqual(sha(SLICE),SLICE_SHA)
        unit=binding['unit_binding'];self.assertEqual(unit['sampling_eligible'],683)
        self.assertEqual(unit['counts']['missing_units'],['cm','in'])
        policy=cfg['type_mix']['streams']['routing'];self.assertEqual(policy['cells']['units']['cents'],100)
        self.assertEqual({n:policy['cells'][n]['cents'] for n in ROUTING},
                         {'camera_displacement':1825,'camera_movement_direction':1588,'camera_rotation':1253,'absolute_distance':1634})
        from student_pilot.type_mix import allocate
        effective,table=allocate(policy,{**{n:20000 for n in ROUTING},'units':683,'recovery':0},1000)
        self.assertEqual(table['units']['cap_cents'],273);self.assertEqual(table['units']['final_cents'],100)
        self.assertIn({'family':'units/in','eligible':64,'reason':'Fewer than 100 eligible rows.'},binding['absent_on_P'])
        with contextlib.redirect_stdout(io.StringIO()):
            replay=regenerate(parent,unit,ROOT/'out/units',Path(authority['frame_map']['path']).parent,
                              cfg['s1_routing']['catalog'],root/'native')
        self.assertEqual(replay,load(ROOT/'out/proof/selection/r.json'))
        # Remove a pin only from an in-memory test authority; retain another valid row.
        first=original[0];request=s1_routing.frame_request(first);key=(request['d'],request['s'],request['i'][0])
        other=next(r for r in original if s1_routing.frame_request(r)['s']!=request['s'])
        frames.frames.pop(key)
        fixture=root/'missing.jsonl';fixture.write_text(''.join(json.dumps(r)+'\n' for r in (first,other)))
        with patch.object(s1_routing,'Frames',return_value=frames):
            refused=pack_slice(fixture,sha(fixture),authority,cfg['s1_routing'],parent,root/'partial.jsonl')
        self.assertEqual(refused['rows'],1);self.assertEqual(refused['refused_rows'],1)
        self.assertEqual(refused['refusals'][0]['qid'],first['qid'])
        self.assertEqual(refused['refusals'][0]['reason'],'requested_frame_absent_from_pinned_map')
        self.assertEqual(refused['refusals'][0]['missing_indices'],[key[2]])
        self.assertEqual(json.loads((root/'partial.jsonl').read_text())['qid'],other['qid'])
        write(ROOT/'out/proof/UNIT_REAL.json',dict(status='PASS',config_identity=binding['config_identity'],
            input_rows=747,packed_rows=747,sealed_validation_pass=747,native_retained=747,refusals=[],
            payload_unchanged=True,all_23904_frame_pins_match=True,rgb_bytes_verified=False,
            missing_frame_refusal_fixture=True,feet_eligible=683,feet_cents=100,feet_cap_cents=273,
            inches_missing=64,program_cells={n:policy['cells'][n]['cents'] for n in ROUTING}))

    def test_printed_census_and_nested_dataset_keys_are_opaque(self):
        from student_pilot import loader_audit as audit
        from collections import Counter
        metadata={'routing':{i:audit.row_metadata({'routing':{'canonical':prefix+'scene'}},'routing','absolute_distance')
                             for i,prefix in enumerate(audit.PREFIXES[:-1])}}
        report={'draw_breakdown':audit.draw_breakdown(metadata,Counter({('routing',i):i+1 for i in range(4)}),routing_available=True)}
        before=copy.deepcopy(report);stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            audit.print_breakdown(report)
            audit.print_record({'nested':[{'ft/scannetppv2':2,'scannet/scene':3,'arkitscenes':4,'scannetpp/':5}]})
        lines=[json.loads(line) for line in stream.getvalue().splitlines()]
        census=lines[0]['loader_draw_breakdown']['routing_absolute_distance']
        self.assertEqual(census['eligible'],{'g0':1,'g1':1,'g2':1,'g3':1,'unknown':0})
        self.assertEqual(census['drawn'],{'g0':1,'g1':2,'g2':3,'g3':4,'unknown':0})
        self.assertEqual(lines[1]['nested'][0],{'ft/g1':2,'g2/scene':3,'g3':4,'g0':5})
        self.assertEqual(report,before)
        path=ROOT/'out/CENSUS_CODES.local.json'
        self.assertEqual(path.read_bytes(),audit.CENSUS_CODE_MAP_BYTES)
        self.assertEqual(lines[0]['census_code_map_sha256'],sha(path))
        for name in ('scannetpp','scannetppv2','scannet','arkitscenes'):self.assertNotIn(name,stream.getvalue())
        op=load(ROOT/'out/OPERATOR.json')
        with tarfile.open(ROOT/'out'/op['archive']) as archive:
            self.assertNotIn(path.name,archive.getnames())
            self.assertNotIn(path.read_bytes(),[archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()])
        with self.assertRaisesRegex(ValueError,'collision'):audit.opaque_keys({'scannetpp/':1,'g0':2})
        write(ROOT/'out/proof/OPAQUE_KEYS.json',dict(status='PASS',config_identity=load(ROOT/'out/BINDING.json')['config_identity'],
            code_map_sha256=sha(path),map_absent_from_archive=True,printed_census=lines[0],nested_keys=lines[1]))

    def test_namespace_probe_argv_has_no_user_home_literal(self):
        path=ROOT/'out/proof/p.py';spec=importlib.util.spec_from_file_location('fix8_proof',path)
        proof=importlib.util.module_from_spec(spec);spec.loader.exec_module(proof)
        root=temp();stub=root/'bw';capture=root/'argv.json'
        stub.write_text('#!'+sys.executable+'\nimport json,os,subprocess,sys\n'
            'json.dump(sys.argv[1:],open(os.environ["PROBE_ARGV"],"w"))\n'
            'i=sys.argv.index("/bin/bash");raise SystemExit(subprocess.call(sys.argv[i:]))\n')
        stub.chmod(0o700);script=proof.namespace_probe(str(stub))
        self.assertNotIn('/home/',script);self.assertNotIn('/home/',path.read_text())
        result=subprocess.run(['bash','-c',script],env={**os.environ,'PROBE_ARGV':str(capture)},text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('preflight PASS',result.stdout)
        argv=load(capture);self.assertEqual(argv[argv.index('--dir')+1],'/home')
        self.assertEqual(argv[argv.index('--tmpfs')+1],'/home')
        self.assertEqual(argv[argv.index('--remount-ro')+1],'/home')
        self.assertIn('--unshare-user',argv);self.assertIn('--uid',argv);self.assertIn('--gid',argv)
        self.assertTrue(all('/home/' not in arg for arg in argv))
        self.assertIn('test -r /proc/self/status && test -w /dev/null && test -d /home',argv[-1])
        write(ROOT/'out/proof/NAMESPACE_ARGV.json',dict(status='PASS',proof_sha256=sha(path),
            config_identity=load(ROOT/'out/BINDING.json')['config_identity'],no_user_home_literal=True,
            argv=argv,scope='Captured bwrap argv and executed inner tests; no namespace or Orchard execution.'))

if __name__=='__main__':unittest.main(verbosity=2)
