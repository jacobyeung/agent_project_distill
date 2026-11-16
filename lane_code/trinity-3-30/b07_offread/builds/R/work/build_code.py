from pathlib import Path
import shutil
root=Path.cwd()
for key in ('vsi','revsi'):
 p=root/'kit'/key/'launcher'
 for name in ('export_stage.py','return_io.py'):
  shutil.copyfile(Path('/scratch/jjyeung/orch_n30/b07_offread/in/readk/kit/launcher')/name,p/name)
 f=p/'orchard_launcher.py';s=f.read_text().replace("'return_io.py', 'ORCHARD_ASSETS.json')","'return_io.py', 'ORCHARD_ASSETS.json', 'export_stage.py', 'gate.py')")
 f.write_text(s)
 f=p/'orchard_results.py';s=f.read_text().replace('/okh7/x27ret','/okh7/9e6b70a213c84fd0').replace('/q8/x27r','/q8/9e6b70a213c84fd0');f.write_text(s)
 f=p/'orchard_stage.py';s=f.read_text();start=s.index("    transport = json.loads(physical(root, config['release']")
 end=s.index("    receipts['videos']",start)
 old=s[start:end]
 s=s[:start]+'''    if config.get('x2') == 1:
        import gate
        gate.before(root, config)
        from export_stage import fetch_and_stage
        receipts['export'] = fetch_and_stage(root, config)
        gate.after(root, config, receipts)
        phase('export_verified')
    else:
'''+''.join('    '+line if line.strip() else line for line in old.splitlines(True))+s[end:]
 f.write_text(s)
 f=p/'orchard_job.py';s=f.read_text().replace("        evidence['staging'] = S.stage(root, config, physical)","        import gate\n        gate.validate(config)\n        evidence['staging'] = S.stage(root, config, physical)\n        gate.after(root, config, evidence['staging'])")
 s=s.replace("str(Path(config['spec']['package'])/'reader/chain.py'), '--root', str(root),","str(root/'bootstrap/gate.py'), '--root', str(root),")
 s=s.replace("        A.atomic_json(source/'metadata/ORCHARD_LAUNCHER.json', evidence)","        A.atomic_json(source/'metadata/ORCHARD_LAUNCHER.json', evidence)\n        A.atomic_json(source/'metadata/X0.json', {k: config.get(k) for k in ('x0', 'x1', 'x2')})")
 f.write_text(s)
