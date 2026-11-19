import hashlib,json,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');W=L/'work/src';O=L/'out'
P=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/a10b_pins')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((P/'export.json').read_text());i=json.loads((P/'1.json').read_text());p=json.loads((P/'PACKAGE.json').read_text())
assert sha(P/'0.json')==p['files']['a/0.json']
assert i['export_pin']['sha256']==sha(P/'export.json') and i['export_pin']['bytes']==(P/'export.json').stat().st_size
assert e['artifact']['sha256']=='5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd'
assert e['step']==400 and p['token']=='dc76460c3a164'
source=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/bind400_partial.json')
b=json.loads(source.read_text())
for k in ('run','step','member_directory','lineage','object'):assert b[k]==e[k]
assert b['preparation_sha256']=={k:v['sha256'] for k,v in e['preparation'].items()}
b.update(config_sha256=e['config_sha256'],archive_sha256=e['archive_sha256'],archive_bytes=sum(x['bytes'] for x in i['archives'][0]['parts']))
assert i['archives'][0]['sha256']==e['archive_sha256']
for n,v in [('BOUND_EXPORT.json',e),('binding.default.json',b),('DEFAULT_EXPORT_PROVENANCE.json',dict(
    source_package='a15_cot_apdc76460c3a164',read='A',job=173060,source=str(P),
    source_pins={n:dict(sha256=sha(P/n),bytes=(P/n).stat().st_size) for n in ('0.json','1.json','export.json','PACKAGE.json')},
    operation_template=dict(path=str(source),sha256=sha(source)),archive_bytes_basis='sum of four authenticated a/1.json part sizes'))]:
    (O/'operations'/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
f=W/'u0/a20.py';s=f.read_text();anchor='PROFILE_KEYS = '
s=s.replace(anchor,'# Read A/job 173060, package a15_cot_apdc76460c3a164; override with --bound-export.\nDEFAULT_BOUND_EXPORT = '+repr(e)+'\n\n'+anchor);f.write_text(s)
# Update fixtures to provide the new evidence and explicitly select their synthetic export.
f=W/'u0/tests/test_round6.py';s=f.read_text().replace('import io\n','import io\nimport inspect\n')
s=s.replace("write(export/'RESTORE.json',{'fixture':'step600'})","write(export/'RESTORE.json',{'fixture':'export'})")
s=s.replace("identity['preparation']=", "identity['artifact']=dict(sha256='a'*64,bytes=123)\n    identity['preparation']=")
s=s.replace("proof['ready'].update(restore=", "write(root/'1.json',dict(export_pin=dict(path='a/export.json',sha256=sha(root/'export-pin.json'),bytes=(root/'export-pin.json').stat().st_size)))\n    proof['inputs']=sha(root/'1.json')\n    proof['ready'].update(restore=")
s=s.replace("required_device_type='H100_80GB')", "adoption_kit=cfg.get('gate_kit_sha256',{}),required_device_type='H100_80GB')",1)
s=s.replace("return config\n\n\ndef gate_receipt", "return config\n\n\ndef selected_gate(helper, args):\n    template=json.loads(Path(args[3]).read_text());root=Path(args[3]).parent\n    if 'bound_export' not in inspect.signature(helper.gate).parameters:return helper.gate(*args)\n    receipts=root/'receipts';receipts.mkdir(exist_ok=True)\n    for source,name in ((Path(template['export'])/'RESTORE.json','RESTORE.json'),(Path(template['artifact_manifest']),'binding.json'),(Path(template['export_pin']),'EXPORT_PIN.json'),(root/'1.json','1.json')):\n        (receipts/name).write_bytes(source.read_bytes())\n    return helper.gate(*args,asset_receipts=receipts,bound_export=template['export_pin'])\n\n\ndef gate_receipt")
s=s.replace('self.helper.gate(*args)', 'selected_gate(self.helper,args)')
s=s.replace("if path.name!='export-pin.json':\n                        with self.assertRaises(ValueError):selected_gate(self.helper,args)", "with self.assertRaises(ValueError):selected_gate(self.helper,args)")
# Preserve the round-6 control: its export-byte mutation was never a round-6 finding.
s=s.replace("with self.assertRaises(ValueError):selected_gate(self.helper,args)\n                finally:path.write_bytes(original)","if not BEFORE or path.name!='export-pin.json':\n                        with self.assertRaises(ValueError):selected_gate(self.helper,args)\n                finally:path.write_bytes(original)",1)
s=s.replace("assertRaisesRegex(ValueError,'export identity')", "assertRaisesRegex(ValueError,'export identity|export pin')")
s=s.replace("name='NVIDIA H100 80GB HBM3',major=9,minor=0,total_memory=80*1024**3)","name='NVIDIA H100 80GB HBM3',major=9,minor=0,total_memory=80*1024**3,multi_processor_count=132)")
s=s.replace("name=n,major=c,minor=0,total_memory=m*1024**3)","name=n,major=c,minor=0,total_memory=m*1024**3,multi_processor_count=132)")
# The old README retains its old directory in before-controls only.
s=s.replace("local=fresh();(local/'step600')", "local_name='step600' if BEFORE else 'adopted'\n        local=fresh();(local/local_name)")
s=s.replace("if '--archive \"$LOCAL/step600/f/0.tgz\"' in b", "if '--archive \"$LOCAL/'+local_name+'/f/0.tgz\"' in b")
s=s.replace("if '(cd \"$LOCAL/step600\"' in block:start=block.index('(cd \"$LOCAL/step600\"')", "if '(cd \"$LOCAL/'+local_name+'\"' in block:start=block.index('(cd \"$LOCAL/'+local_name+'\"')")
s=s.replace("(local/'step600/unpack-success.json')", "(local/local_name/'unpack-success.json')")
f.write_text(s)
f=W/'u0/tests/test_round5.py';s=f.read_text()
s=s.replace("config=helper.gate(target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'settings.json',root/'config.json')", "config=fixtures.selected_gate(helper,(target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'settings.json',root/'config.json'))")
s=s.replace("self.assertIn('--out \"$LOCAL/step600/ret\" > \"$LOCAL/step600/unpack-success.json\"',readme)","local_name='step600' if BEFORE else 'adopted'\n        self.assertIn('--out \"$LOCAL/'+local_name+'/ret\" > \"$LOCAL/'+local_name+'/unpack-success.json\"',readme)")
f.write_text(s)
# Let the real CPU-proof fixture execute tar; only translate the namespace's -C path.
f=W/'u0/tests/test_round4.py';s=f.read_text();needle="    def execute(argv,**kwargs):\n"
s=s.replace(needle,needle+"        if argv[0]=='/bin/tar':\n            argv=list(argv);argv[argv.index('-C')+1]=str(physical(root,argv[argv.index('-C')+1]))\n            return subprocess.run(argv,**kwargs)\n")
f.write_text(s)
print('Default binding reconstructed from supplied step-400 pins; code and fixture evidence updated.')
