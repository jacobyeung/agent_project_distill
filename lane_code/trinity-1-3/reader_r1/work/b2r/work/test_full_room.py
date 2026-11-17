"""Empty-root rehearsal through the allocated operator, using explicit CPU fixtures."""
import copy,hashlib,io,json,sys,tarfile,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src'
sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P)]
import torch,scipy
from PIL import Image
from e2e_reader import parity
from parity_kit.common import FRAMES,DENSE
from orchard_h10.common import write,sha,template,read_config,canonical
from orchard_h10 import job,prepare
from parity_kit import stage_restore,build_manifest
import tower_sequence as T
import node_check as N

class Full(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path(tempfile.mkdtemp(prefix='cpu_empty_',dir=W/'work/tmp'))
  cls.cfg=read_config(O/'package');cls.inputs=json.loads((O/'inputs_tower.json').read_text())
  cls.S,cls.J,*_=template()
  cls.manifest=json.loads((P/'items/room134.json').read_text())
  cls.item=next(r for r in cls.manifest['items'] if r['id'] in cls.manifest['sets']['dev-S1'])
  # Exercise the complete production admission, including the d/f destination.
  job.check_inputs(cls.inputs,cls.cfg,package=O/'package')
  bad=copy.deepcopy(cls.inputs);bad['archives'][-1]['destination']+='/escape'
  with unittest.TestCase().assertRaisesRegex(ValueError,'stable data root'):
   job.check_inputs(bad,cls.cfg,package=O/'package')
  frame_root=cls.J.physical(cls.root,cls.inputs['frames_root'])
  cls.frame_root=frame_root
  assert not frame_root.exists()
  source=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/assets/d81f4a26.tar')
  spec=cls.inputs['archives'][-1]
  assert source.stat().st_size==spec['parts'][0]['bytes'] and sha(source)==spec['sha256']
  # Read the tar in place. Use the production extractor and exact admitted destination.
  with source.open('rb') as stream:
   cls.S.extract_stream(stream,cls.root/spec['destination'],None,spec['expanded_bytes'],links=True)
  captures=copy.deepcopy(parity._captures(FRAMES));dense=copy.deepcopy(parity._captures(DENSE))
  cls.original_c=copy.deepcopy(captures);cls.original_d=copy.deepcopy(dense)
  fixtures={};key=cls.item['native'];assert key.startswith('d1/')
  for i,f in enumerate(dense[key]['frames']):
   buf=io.BytesIO();Image.new('RGB',(64,48),(i,20,70)).save(buf,format='PNG');raw=buf.getvalue()
   rel=str(Path(f['path']).relative_to('/scratch/jjyeung/devs1_frames'))
   fixtures['f/'+rel]=raw
   # Also stage the requested native d1/<scene> layout, with its explicit fixture manifest.
   fixtures['f/'+key+f'/{f["index"]:06d}.png']=raw
   f['sha256']=hashlib.sha256(raw).hexdigest()
  lookup={f['index']:f for f in dense[key]['frames']}
  for f in captures[key]['frames']:f['sha256']=lookup[f['index']]['sha256']
  archive=cls.root/'fixture.tar'
  with tarfile.open(archive,'w') as tar:
   for name,raw in fixtures.items():
    m=tarfile.TarInfo(name);m.size=len(raw);tar.addfile(m,io.BytesIO(raw))
  # Dev-S1 archive unpacks to d, and its f/ subtree becomes the same frame root.
  with archive.open('rb') as stream:
   cls.S.extract_stream(stream,cls.root/cls.inputs['archives'][0]['destination'],None,sum(map(len,fixtures.values())),links=True)
  cls.captures=captures;cls.dense=dense
  cls.logical=cls.J.physical(cls.root,cls.cfg['logical'])
  # Real preparation; unavailable export weights and environment versions are labelled stubs.
  inp=json.loads(json.dumps(cls.inputs).replace(cls.cfg['logical'],str(cls.logical)));inp['_export']=json.loads((O/'export_544.json').read_text())
  modules={'torchvision':NS(__name__='torchvision',__version__='fixture'), 'transformers':NS(__name__='transformers',__version__='5.12.0')}
  versions=dict(torch=torch.__version__,torchvision='fixture',transformers='5.12.0',scipy=scipy.__version__)
  write(Path(inp['files'][inp['environment_receipt']]['path']),dict(versions=versions))
  def restore(*a,**k):write(Path(a[3])/'RESTORE.json',dict(synthetic_restore=True))
  policy={k:v for k,v in T.descriptors(P)[0].items() if k in ('stage1_select_rule','perception_memo','perception_memo_verify_ids','perception_memo_modules','save_own_depth')}
  with patch.dict(sys.modules,modules),patch.object(stage_restore,'stage',restore),patch.object(build_manifest,'build',return_value={'synthetic_artifact':True}):
   prepare.run(dict(logical=str(cls.logical),**policy),inp)
  cls.settings=json.loads((cls.logical/'d/settings.json').read_text())
  cls.settings.update(frames_json={'captures':captures},dense_manifest={'captures':dense})
  cls.base=dict(package=str(P),python=sys.executable,export=str(cls.logical/'d/e'),binding=str(cls.logical/'d/binding.json'),
    export_pin=str(cls.logical/'d/6.json'),plan_sha256=cls.cfg['plan_sha256'],inputs_sha256=canonical(cls.inputs),
    operator_sha256=sha(O/'tower_sequence.py'),device='cpu',prefix=[],measure_memory=True)

 def config(self,label,settings=None):
  path=self.root/(label+'.json');write(path,settings or self.settings)
  return dict(self.base,settings=str(path),output=str(self.root/label))

 def test_empty_root_exact_staged_paths(self):
  config=self.config('archive_layout')
  result=T.rehearsal(config);full=N.validate_full_reader(result)
  T.memory_probe(config)
  self.assertTrue(full['passed']);self.assertEqual(len(full['records']),2)
  for r in full['records']:
   self.assertTrue(r['record']['complete'])
   self.assertTrue(all(Path(f['path']).is_relative_to(self.frame_root) for f in r['frames']))
  write(O/'LOCAL_CPU_CHECK.json',dict(passed=True,synthetic_devs1=True,root=str(self.root),
    r0_tar_sha256=self.inputs['archives'][-1]['sha256'],native=self.item['native'],
    admission='real check_inputs including d/f and escape refusal',staging='real extract_stream at admitted d and d/f destinations',
    stubbed_preparation=['export weights restore','artifact build','runtime versions'],full_reader=full))

 def test_native_d1_layout(self):
  settings=copy.deepcopy(self.settings);key=self.item['native']
  for kind in ('frames_json','dense_manifest'):
   for f in settings[kind]['captures'][key]['frames']:f['path']=key+f'/{f["index"]:06d}.png'
  result=T.rehearsal(self.config('native_layout',settings));full=N.validate_full_reader(result)
  self.assertTrue(all('/d/f/d1/scene0155_00/' in f['path'] for f in full['records'][0]['frames']))
  write(O/'LOCAL_NATIVE_CPU_CHECK.json',dict(passed=True,synthetic_devs1=True,native=key,full_reader=full))

 def test_digest_failure_aborts_check(self):
  settings=copy.deepcopy(self.settings);key=self.item['native']
  for kind in ('frames_json','dense_manifest'):
   settings[kind]['captures'][key]['frames'][0]['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'sha256 mismatch'):
   T.rehearsal(self.config('bad_digest',settings))
  self.assertFalse((self.root/'bad_digest/REHEARSAL.json').exists())

 def test_decode_failure_aborts_check(self):
  # Match the digest to invalid bytes so the real decoder, not the hash check, refuses.
  settings=copy.deepcopy(self.settings);key=self.item['native'];p=self.frame_root/'invalid.png';p.write_bytes(b'not a PNG')
  for kind in ('frames_json','dense_manifest'):
   f=settings[kind]['captures'][key]['frames'][0];f.update(path='invalid.png',sha256=sha(p))
  with self.assertRaisesRegex(OSError,'cannot identify image'):
   T.rehearsal(self.config('bad_decode',settings))

 def test_helper_rejects_incomplete_or_missing(self):
  with self.assertRaises(KeyError):N.validate_full_reader([{}])
  with self.assertRaises(ValueError):N.validate_full_reader([{'full_reader':dict(passed=False,device='cpu')}])
  proof=json.loads((O/'LOCAL_CPU_CHECK.json').read_text())['full_reader'] if (O/'LOCAL_CPU_CHECK.json').exists() else N.validate_full_reader(T.rehearsal(self.config('receipt')))
  for change in ('missing','unfinished','wrong_score','false_pass'):
   full=copy.deepcopy(proof)
   if change=='missing':full['records'].pop()
   elif change=='unfinished':full['records'][0]['record']['complete']=False
   elif change=='wrong_score':full['records'][0]['official_score']['score']=-1
   else:full['records'][0]['passed']=False
   with self.assertRaises(ValueError):N.validate_full_reader([{'full_reader':full}])

if __name__=='__main__':unittest.main(verbosity=2)
