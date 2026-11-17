"""Run each sealed source tree in its own interpreter and report room bindings."""
import contextlib,io,json,sys
from pathlib import Path
source,out=map(Path,sys.argv[1:]);sys.path[:0]=[str(source/'b'),str(source/'tree'),str(source)]
from orchard_h10.common import write
from h1eval.items import load_manifest,digest
from h1eval.h10 import parity_adapter as A,launch
from e2e_reader import parity
from parity_kit.common import FRAMES,DENSE
name='room134' if (source/'items/room134.json').exists() else 'devs1_routed'
m=load_manifest(source/'items'/f'{name}.json');rows=[r for r in m['items'] if r['question_type']=='room_size_estimation' and not r['id'].startswith('r0_')]
settings=dict(frames_root='/scratch/jjyeung/b01ec87a6f29b/d/f',arm='own_depth',stage1_select_rule='null_argmax',
 perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['room_size_estimation'])
mapped,receipt=A.map_items(m['items'],settings,name=name)
c=parity._captures(settings.get('frames_json',FRAMES));d=parity._captures(settings.get('dense_manifest',DENSE))
policy={k:settings[k] for k in ('arm','stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth','types')}
result=[]
for row in rows:
 task=mapped[row['id']];b=parity.bind_item(task,settings,verify=False)
 result.append(dict(id=row['id'],type=row['question_type'],task=task,frames=b,
  mapping=next(r for r in receipt['items'] if r['id']==row['id']),
  anchor_capture=c[row['native']],dense_capture=d[row['native']],settings=policy,
  require_dense64=settings.get('require_dense64',False)))
write(out/'e/RESTORE.json',{});write(out/'binding.json',dict(root=str(out),name='fixture',sha256='a'*64))
settings.update(export_dir=str(out/'e'),artifact_manifest=str(out/'binding.json'));write(out/'settings.json',settings)
write(out/'pin.json',dict(lineage='SFT',step=544))
args=launch.parser().parse_args(['--items',str(source/'items'/f'{name}.json'),'--export',str(out/'e'),
 '--artifact-manifest',str(out/'binding.json'),'--reader-root',str(source/'b'),'--out',str(out/'journal'),
 '--export-pin',str(out/'pin.json'),'--settings',str(out/'settings.json'),'--types','room_size_estimation',
 '--arms','tower','--modes','none','--device','cpu','--type-journals'])
def maker(*a,**k):return lambda item:dict(text='<think></think><answer>21.52</answer>',finish='eos')
with contextlib.redirect_stdout(io.StringIO()):launch.run_types(args,make_real=maker)
records=launch.read_records(out/'journal/4/0/items.jsonl');env=json.loads((out/'journal/4/0/environment.json').read_text())
assert {r['type'] for r in records}=={'room_size_estimation'}
assert env['settings']['types']==['room_size_estimation']
assert all(env['binding'][k]==policy[k] for k in policy if k not in ('types','arm'))
write(out/'SNAPSHOT.json',dict(rows=result,records=[dict(id=r['id'],type=r['type'],arm=r['arm'],mode=r['mode'],complete=r['complete']) for r in records if r['id'] in {r['id'] for r in rows}],
 types=env['settings']['types'],policy=policy,durable_types=env['binding'].get('types'),digests_read_from_pinned_metadata=True))
