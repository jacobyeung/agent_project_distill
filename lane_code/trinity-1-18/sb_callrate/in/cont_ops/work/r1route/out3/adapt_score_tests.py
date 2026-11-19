from pathlib import Path
W=Path(__file__).resolve().parent
s=(W/'test_score_r1route.py').read_text();start=s.index(' def fixture(self):');end=s.index(' def test_wrong_step_and_rule_refused',start)
body=''' def fixture(self):
  # Rebuild only a small negative-admission fixture. This is not a saved job return.
  import hashlib
  root=Path(tempfile.mkdtemp(prefix='score_',dir=O/'test_tmp'));oldbase=S.BASE
  self.addCleanup(setattr,S,'BASE',oldbase)
  base=root/'synthetic_baseline';pkg=base/'b1';pkg.mkdir(parents=True)
  for name in ('src','package'):(pkg/name).symlink_to(oldbase/'b1'/name,target_is_directory=True)
  for name in ('READ_PLAN.json','tower_sequence.py'):(pkg/name).write_bytes((oldbase/'b1'/name).read_bytes())
  (base/'SYNTHETIC_FIXTURE.json').write_text('{"baseline_measurement":false}\\n')
  S.BASE=base
  plan=S.read(pkg/'READ_PLAN.json');public=S.read(pkg/'package/0.json');manifest=S.read(pkg/'src/items/devs1_routed.json')
  identity=dict(plan=public['plan_sha256'],operator_sha256=S.digest(pkg/'tower_sequence.py'),reads=plan['read_settings'])
  src=pkg/'work/ret';(src/'metadata').mkdir(parents=True);(src/'metadata/IDENTITY.json').write_text(json.dumps(identity))
  expected=plan['read_settings'][0]
  settings={k:expected[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')}
  binding=dict(settings,arms=['tower'],modes=[{'name':'none'}],step=544,lineage='SFT',fixture=False,items_sha256=S.digest(pkg/'src/items/devs1_routed.json'),item_set_sha256=manifest['item_set_sha256'],settings_sha256=S.canonical(settings),export_sha256='fixture',artifact_manifest_sha256='fixture')
  from h1eval.cli import code_hash
  from h1eval.h10.parity_adapter import reader_code_hash
  from h1eval.h10 import parity_adapter
  binding.update(reader_sha256=code_hash(pkg/'src/b/e2e_reader'),parity_code_sha256=reader_code_hash(pkg/'src/b'),evaluator_code_sha256=code_hash(),maker_sha256=S.digest(Path(parity_adapter.__file__)))
  baseline_journal=src/'metadata/reads/0/metadata/journals/0/0';baseline_journal.mkdir(parents=True)
  (baseline_journal/'environment.json').write_text(json.dumps(dict(binding=binding,settings=settings)))
  ret=root/'candidate';(ret/'metadata').mkdir(parents=True);(ret/'metadata/IDENTITY.json').write_text(json.dumps(identity))
  d=ret/'metadata/reads/0/metadata/journals/0/0';d.mkdir(parents=True)
  (d/'environment.json').write_bytes((baseline_journal/'environment.json').read_bytes());(d/'STARTED.json').write_text('{}\\n')
  item=manifest['items'][0];row=dict(id=item['id'],room_key=item['room_key'],type=item['question_type'],arm='tower',mode='none',complete=True,output=dict(text='<answer>1</answer>',finish='eos',scores={'answer':1},calls={'records':[]}))
  (d/'items.jsonl').write_text(json.dumps(row)+'\\n')
  return ret,d
'''
s=s[:start]+body+s[end:]
# Relative tests must point to the shared out2 fixture and bases.
s=s.replace("O=Path(__file__).resolve().parent", "HERE=Path(__file__).resolve().parent\nO=HERE.parent if HERE.name in ('A','B') else HERE\n(O/'test_tmp').mkdir(exist_ok=True)")
for d in (W,W/'A',W/'B'):(d/'test_score_r1route.py').write_text(s)
