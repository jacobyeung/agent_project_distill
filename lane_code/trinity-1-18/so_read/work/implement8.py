from pathlib import Path
import json,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0';O=L/'out'
def edit(p,old,new):
 s=p.read_text();assert old in s,(str(p),old[:120]);p.write_text(s.replace(old,new))
# Run both the link admission and tar in the live namespace. System Python is
# available in A4's /usr bind even when the staged interpreter cannot start.
p=L/'work/operator4/package/a/5.py'
edit(p,'def stage_gate_assets(root, cfg, J, destination, checked_run, env):','''GATE_ARCHIVE = """import os,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
def fail(error):raise error
for base,dirs,files in os.walk(str(root),followlinks=False,onerror=fail):
    for name in dirs+files:
        path=Path(base)/name
        if path.is_symlink():
            try:target=path.resolve(strict=True)
            except (OSError,RuntimeError) as error:raise ValueError('Invalid symlink: '+str(path)) from error
            if target!=root and root not in target.parents:
                raise ValueError('Symlink target leaves logical/d: '+str(path))
os.execv('/bin/tar',['/bin/tar','-cf','-','-C',str(root),'.'])
"""


def stage_gate_assets(root, cfg, J, destination, checked_run, env, results=None):''')
edit(p,"    with destination.open('xb') as stream:\n        checked_run(J.namespace(root)+['/bin/tar','-chf','-','-C',cfg['logical']+'/d','.'],\n                    env=env,stdout=stream,stderr=subprocess.PIPE,check=True)","    with destination.open('xb') as stream, (Path(results) if results is not None else destination.parent).joinpath('4.err').open('wb') as errors:\n        checked_run(J.namespace(root)+['/usr/bin/python3','-I','-s','-B','-c',GATE_ARCHIVE,cfg['logical']+'/d'],\n                    env=env,stdout=stream,stderr=errors,check=True)")
edit(p,"('manifest.json','manifest.json'),('6.json','EXPORT_PIN.json')", "('manifest.json','manifest.json'),('6.json','EXPORT_PIN.json'),('ENVIRONMENT.json','ENVIRONMENT.json')")
edit(p,"stage_gate_assets(root,cfg,J,package/'a/4.tar',checked_run,env)","stage_gate_assets(root,cfg,J,package/'a/4.tar',checked_run,env,results=results)")
# Preserve OFF prepare bytes; ON records the compiled CUDA version and binds it.
p=E/'a18.py'
edit(p,"    write(d/'ENVIRONMENT.json',dict(versions=versions,python=sys.executable))", "    environment=dict(versions=versions,python=sys.executable)\n    if config.get('read_extensions') is True:environment['cuda']=torch.version.cuda\n    write(d/'ENVIRONMENT.json',environment)")
edit(p,"restore=sha(export/'RESTORE.json')))","restore=sha(export/'RESTORE.json'),\n        **(dict(environment=sha(d/'ENVIRONMENT.json')) if config.get('read_extensions') is True else {})))")
# One immutable reviewed identity shared by builder and gate.
p=E/'a20.py';s=p.read_text();line=next(l for l in s.splitlines() if l.startswith('DEFAULT_BOUND_EXPORT = '))
fixed=json.loads((O/'operations/binding.default.json').read_text())
keys=('run','step','member_directory','lineage','object','config_sha256','archive_sha256','preparation_sha256','archive_bytes','base_identity','frame_layout')
fixed={k:fixed[k] for k in keys}
p=E/'a19.py';edit(p,'def checked_binding(path):',line+'\nFIXED_BINDING = '+repr(fixed)+'\n\n\ndef checked_binding(path):')
edit(p,"    binding = checked_binding(export_binding)\n", "    binding = checked_binding(export_binding)\n    if any(binding.get(k) != v for k,v in FIXED_BINDING.items()):\n        raise ValueError('Require the reviewed step-400 export identity and preparation')\n")
p=E/'a20.py';edit(p,'from u0.a19 import checked_binding, sha, tarbytes, unpack','from u0.a19 import checked_binding, sha, tarbytes, unpack, DEFAULT_BOUND_EXPORT')
edit(p,'# Read A/job 173060, package a15_cot_apdc76460c3a164; override with --bound-export.\n'+line,'# Only read A/job 173060, package a15_cot_apdc76460c3a164 can authorize adoption.')
edit(p,'asset_receipts=None, bound_export=None):','asset_receipts=None):')
edit(p,"    selected = read(bound_export) if bound_export else DEFAULT_BOUND_EXPORT\n    if identity != selected:\n        raise ValueError('Staged export differs from selected export (default: reviewed step 400)')", "    if identity != DEFAULT_BOUND_EXPORT:\n        raise ValueError('Staged export differs from reviewed step-400 export')\n    environment_path = Path(asset_receipts)/'ENVIRONMENT.json' if asset_receipts else Path(config['environment_receipt'])\n    environment = read(environment_path)\n    environment_sha = sha(environment_path.read_bytes())\n    if environment_sha != receipt['ready']['environment']:\n        raise ValueError('Environment receipt differs from CPU proof')\n    adoption_environment = dict(sha256=environment_sha,torch=environment['versions']['torch'],\n        transformers=environment['versions']['transformers'],cuda=environment['cuda'])")
edit(p,"                  adoption_kit=cfg['gate_kit_sha256'],", "                  adoption_kit=cfg['gate_kit_sha256'],adoption_environment=adoption_environment,")
edit(p,"    g.add_argument('--bound-export',help='Reviewed export.json; defaults to the pinned step-400 export from read A/job 173060')\n",'')
edit(p,'a.config_out,a.asset_receipts,a.bound_export)','a.config_out,a.asset_receipts)')
edit(p,"print(json.dumps(dict(passed=True,pool_bytes=total)))", "environment=json.loads((p/'a/c/ENVIRONMENT.json').read_text())\nenvironment_sha=h(p/'a/c/ENVIRONMENT.json')\nif environment_sha!=proof['ready']['environment']:raise ValueError('CPU environment receipt differs')\nexpected_environment=dict(sha256=environment_sha,torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])\nif gate.get('adoption_environment')!=expected_environment:raise ValueError('GPU gate environment versions/hash differ')\nprint(json.dumps(dict(passed=True,pool_bytes=total)))")
p=O/'kit_parity50/run.py'
edit(p,'def validate_device(cfg, torch):', '''def validate_environment(cfg):
    import torch
    import transformers
    path=Path(cfg['environment_receipt'])
    environment=json.loads(path.read_bytes())
    expected=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])
    actual=dict(sha256=expected['sha256'],torch=torch.__version__,transformers=transformers.__version__,cuda=torch.version.cuda)
    if not actual['cuda'] or actual!=expected or expected!=cfg.get('adoption_environment'):
        raise ValueError('GPU environment versions/hash differ from CPU proof')
    return actual


def validate_device(cfg, torch):''')
edit(p,"    record['adoption_kit'] = kit_hashes()", "    record['adoption_kit'] = kit_hashes()\n    record['adoption_environment'] = validate_environment(cfg)")
edit(p,'    validate_assets(cfg)\n','    validate_assets(cfg)\n    validate_environment(cfg)\n')
edit(p,"                transformers=transformers.__version__,cuda=torch.version.cuda,", "                transformers=transformers.__version__,cuda=torch.version.cuda,\n                adoption_environment=validate_environment(cfg),")
# Ensure runtime preflight happens before any extension activation or reader import.
edit(p,"    source=Path(cfg['original_source_root'] if mode=='ORIGINAL' else cfg['source_root']).resolve()", "    validate_environment(cfg)\n    source=Path(cfg['original_source_root'] if mode=='ORIGINAL' else cfg['source_root']).resolve()")
(L/'work/STATUS.md').write_text(subprocess.check_output(['date','-u'],text=True)+'''Round 8 in progress. Reviewed verdict read in full; out_round8 and source snapshot preserve reviewed bytes.
Eight regressions reproduce the defects before changes. Archive admission and tar execute inside the live namespace; links remain links and stderr persists.
ON preparation records and pins CUDA with the environment. Gate/submit bind versions and the receipt hash. Builder rejects every non-step-400 identity before reading base files.
Next: update fixtures and README, run full validation, regenerate patches and seal delivery. Deadline 18:30:31 UTC.
''')
print('Implemented archive, environment and fixed-export changes.')
