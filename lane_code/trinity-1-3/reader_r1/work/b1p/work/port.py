from pathlib import Path
import tarfile, re, shutil, secrets, json
W=Path.cwd(); O=W/'out'; R=W/'in/repin/out'; B=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1')
for folder in ('src','baseline'):
 with tarfile.open(R/'0.tgz') as t:
  for m in t:
   assert m.isfile() and '..' not in Path(m.name).parts and not Path(m.name).is_absolute()
   p=O/folder/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
# Apply the B1 reader hunks to the reviewed payload; keep production builder and admission unchanged.
patch=(B/'out/PATCH.diff').read_text()
selected=['b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','h1eval/h10/depth_snapshot.py','h1eval/h10/launch.py','h1eval/h10/perception_own.py','h1eval/perception.py','orchard_h10/runner.py']
for section in re.split(r'(?m)(?=^--- )',patch):
 if not section.startswith('--- '):continue
 lines=section.splitlines(True);name=lines[1].strip()[6:]
 if name not in selected:continue
 p=O/'src'/name;s=p.read_text() if p.exists() else ''
 for h in re.split(r'(?m)^@@.*?@@.*\n',''.join(lines[2:]))[1:]:
  h=h.replace("lineage='SFT',step=544","lineage=identity['lineage'],step=identity['step']") if name=='h1eval/h10/launch.py' else h
  old=''.join(l[1:] for l in h.splitlines(True) if l.startswith((' ','-')))
  new=''.join(l[1:] for l in h.splitlines(True) if l.startswith((' ','+')))
  assert s.count(old)==1 or not old,(name,old[:100])
  s=s.replace(old,new,1) if old else new
 p.write_text(s)
def edit(name,a,b):
 p=O/'src'/name;s=p.read_text();assert s.count(a)==1,(name,a);p.write_text(s.replace(a,b))
edit('h1eval/h10/launch.py',"get('save_own_depth', True)","get('save_own_depth', False)")
# Reuse is a resume path and must bind the selector rule too.
edit('h1eval/h10/launch.py',"'artifact_manifest_sha256'):","'artifact_manifest_sha256','stage1_select_rule'):")
edit('b/e2e_reader/real.py','selector_head=None, serve_room=False):',"selector_head=None, serve_room=False, stage1_select_rule='null_argmax'):")
edit('b/e2e_reader/real.py','stage1_factory(sam3_tower, selector_head, anchor_frames)', 'stage1_factory(sam3_tower, selector_head, anchor_frames, rule=stage1_select_rule)')
edit('h1eval/perception.py','scale_head=None,**kw):',"scale_head=None,stage1_select_rule='null_argmax',**kw):")
edit('h1eval/perception.py','sam3_tower=sam3_tower,selector_head=selector_head)', 'sam3_tower=sam3_tower,selector_head=selector_head,stage1_select_rule=stage1_select_rule)')
edit('h1eval/perception.py','stage1_factory(sam3_tower,selector_head,anchor_frames)', 'stage1_factory(sam3_tower,selector_head,anchor_frames,rule=stage1_select_rule)')
p=O/'src/b/e2e_reader/parity.py';s=p.read_text();s=s.replace('default_perception = real_perception(artifact, device=device, scale_head=scale,',"default_perception = real_perception(artifact, device=device, scale_head=scale,\n                                             stage1_select_rule=settings.get('stage1_select_rule','null_argmax'),")
p.write_text(s)
# The normal package remains the reviewed defaults. Operator settings select a read.
edit('orchard_h10/prepare.py',"env_roots=inputs.get('env_roots',[]),arm='own_depth')", "env_roots=inputs.get('env_roots',[]),arm='own_depth',\n        stage1_select_rule=config.get('stage1_select_rule','null_argmax'),\n        save_own_depth=config.get('save_own_depth',False))")
# Runner has explicit arm binding for the operator-side configuration.
for name in ('orchard_h10/runner.py',):
 p=O/'src'/name;s=p.read_text().replace("'--arms','own'","'--arms',','.join(config.get('arms',['own']))").replace("plan(chosen,['own'],","plan(chosen,config.get('arms',['own']),").replace("types=types,arms=['own'],","types=types,arms=config.get('arms',['own']),")
 p.write_text(s)
for name in ('build_package.py','fill_export.py','export_544.json','inputs_544.json','EXPORT_SCHEMA.md','AUDIT_R1.json'):
 shutil.copyfile(R/name,O/name)
p=O/'build_package.py';s=p.read_text().replace("OUT/'production/9.json'","OUT/'baseline/9.json'").replace("names.add('orchard_h10/export_pins.py')","names.add('h1eval/h10/depth_snapshot.py')");p.write_text(s)
(O/'TOKEN').write_text('e'+secrets.token_hex(6)+'\n')
# Test/reference paths stay read-only; generated fixtures stay here.
(O/'tests').mkdir(exist_ok=True)
for name in ('test_package.py','test_constraints.py'):
 s=(R/'tests'/name).read_text()
 if name=='test_package.py':
  s=s.replace("PROD=OUT/'production'",f"PROD=Path({str(R/'production')!r})")
  s=s.replace("ROOT/'in/",f"Path({str(W/'in/repin')!r})/'in/")
  s=s.replace("self.assertEqual(code_hash(SRC/'b/e2e_reader'),old['reader'])","self.assertNotEqual(code_hash(SRC/'b/e2e_reader'),old['reader'])")
  s=s.replace("'h1eval/h10/launch.py','b/parity_kit/stage_restore.py'}", "'h1eval/h10/launch.py','b/parity_kit/stage_restore.py',"+repr(set(selected)-{'orchard_h10/runner.py','h1eval/h10/launch.py'})[1:-1]+",'b/e2e_reader/real.py','b/e2e_reader/parity.py'}")
 else:
  s=s.replace("ROOT = Path(__file__).resolve().parents[2]",f"ROOT = Path({str(W/'in/repin')!r})")
  s=s.replace("(ROOT/'out/TOKEN')",f"(Path({str(O/'TOKEN')!r}))")
 (O/'tests'/name).write_text(s)
for name in ('test_b1.py','test_select_stubs.py'):
 s=(B/'work'/name).read_text().replace("W/'work/p", "W/'out/src").replace("W/'in/pkg/p", "W/'out/baseline")
 (W/'work'/name).write_text(s)
for name in ('b1_report.py','test_b1_report.py'):shutil.copyfile(B/'out'/name,O/name)
print('token', (O/'TOKEN').read_text().strip())
print('changed', [str(p.relative_to(O/'src')) for p in (O/'src').rglob('*.py') if not (O/'baseline'/p.relative_to(O/'src')).exists() or p.read_bytes()!=(O/'baseline'/p.relative_to(O/'src')).read_bytes()])
