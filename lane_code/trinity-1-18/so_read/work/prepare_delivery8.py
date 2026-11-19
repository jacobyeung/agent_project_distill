from pathlib import Path
import json,subprocess,hashlib
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
p=O/'FRAMEWORK_EVIDENCE.md';s=p.read_text();s+='''
## Environment admission

The gate compares exact strings from `torch.__version__`, `transformers.__version__` and `torch.version.cuda` with the CPU-bound ENVIRONMENT.json. The installed [torch import:60](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/__init__.py:60) imports the version from [torch_version.py:66](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/torch_version.py:66), which wraps the generated version. The installed [version.py:4](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4) records `2.11.0+cpu`; [line 6](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:6) records `cuda=None`. The installed [transformers version:21](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/__init__.py:21) records `5.12.1`. These are build/library versions, not a measurement of the GPU driver version.

The GPU shell preflight separately requires CUDA availability. The installed [is_available:161](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/cuda/__init__.py:161) returns false without compiled CUDA support and otherwise checks device availability. The official [is_available reference](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.is_available.html) and [CUDA versus HIP check](https://docs.pytorch.org/docs/2.11/notes/hip.html#checking-for-hip) support the distinction between availability and `torch.version.cuda`. These pages and the device-properties reference were read on 2026-11-19. Tests use CUDA/version test doubles; the CPU environment never queries a GPU.

Only ON prepare adds `cuda` and the environment hash to READY; ordinary prepare bytes remain unchanged. A matching version receipt does not prove that the archived interpreter starts outside bwrap. The executable README preflight checks that on the allocated host before gate work. Its versions and file hash must also match in the driver, every worker, ue.json and SUBMIT_CHECK.
''';p.write_text(s)
# Derive a fresh documentation/source check from the retained bounded checker.
s=(L/'work/docs_check7.py').read_text().replace("SOURCE_EVIDENCE7.json","SOURCE_EVIDENCE8.json").replace("'673-690'","'161-180,673-695'")
s=s.replace("files=[base/'cuda/__init__.py',base/'_C/__init__.pyi']", "files=[base/'cuda/__init__.py',base/'_C/__init__.pyi',base/'version.py',base/'torch_version.py',base/'__init__.py',base.parent/'transformers/__init__.py']")
s=s.replace("official_pages_read_utc='2026-11-19T16:36:06Z'", "official_pages_read_utc='2026-11-19T17:39:40Z'")
s=s.replace("official_pages=['https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html']", "official_pages=['https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html','https://docs.pytorch.org/docs/2.11/generated/torch.cuda.is_available.html','https://docs.pytorch.org/docs/2.11/notes/hip.html#checking-for-hip']")
s += "\nassert '--bound-export' not in text and 'For a different target' not in text\nassert 'tar -cf - -C <logical>/d .' in text and '33 GB, estimated' in text\nprint('PASS: step-400-only handoff, symlink archive, version preflight, retained stderr and 33 GB estimate documented.')\n"
(L/'work/docs_check8.py').write_text(s)
# The integration runs on the fresh applied tree and its real CPU-job fixture.
s=(L/'work/gate_integration7.py').read_text().replace('gate-probe7-','gate-probe8-').replace('retained-data7','retained-data8').replace('public_kit7','public_kit8')
s=s.replace("export_pin=str(d/'6.json'))", "export_pin=str(d/'6.json'),environment_receipt=str(d/'ENVIRONMENT.json'))")
start=s.index('try:gate(*args)');end=s.index("cmd=[sys.executable",start)
s=s[:start]+"config=gate(*args)\n"+s[end:]
s=s.replace("for name in ('CPU.json','MEMORY.json'):","for name in ('CPU.json','MEMORY.json','ENVIRONMENT.json'):")
s=s.replace("kit.write_gate_receipt(out,config,True);", "# CPU fixture has cuda=None: simulate only runtime CUDA/version imports for receipt serialization.\n# This is explicitly synthetic and cannot establish production GPU parity.\nfrom unittest.mock import patch\nimport types\nenv_record=json.loads((d/'ENVIRONMENT.json').read_text())\nenv_record['cuda']='12.9'\n(d/'ENVIRONMENT.json').write_text(json.dumps(env_record))\n(proof/'ENVIRONMENT.json').write_bytes((d/'ENVIRONMENT.json').read_bytes())\ncpu['ready']['environment']=sha(d/'ENVIRONMENT.json')\n(package/'a/c/ENVIRONMENT.json').write_bytes((d/'ENVIRONMENT.json').read_bytes())\n(package/'a/c/CPU.json').write_text(json.dumps(cpu))\nconfig['adoption_environment']=dict(sha256=sha(d/'ENVIRONMENT.json'),torch=env_record['versions']['torch'],transformers=env_record['versions']['transformers'],cuda='12.9')\nfake_torch=types.SimpleNamespace(__version__=env_record['versions']['torch'],version=types.SimpleNamespace(cuda='12.9'))\nfake_transformers=types.SimpleNamespace(__version__=env_record['versions']['transformers'])\nwith patch.dict(sys.modules,torch=fake_torch,transformers=fake_transformers):\n    kit.write_gate_receipt(out,config,True)\n")
s=s.replace("kit.write_gate_receipt(out,config,False);", "with patch.dict(sys.modules,torch=fake_torch,transformers=fake_transformers):\n    kit.write_gate_receipt(out,config,False)\n")
s=s.replace('default400 refuses synthetic600, explicit selection passes.','only reviewed step400 passes; synthetic environment evidence binds submit.')
s=s.replace("required_device_type=config['required_device_type']", "required_device_type=config['required_device_type'],environment=config['adoption_environment']")
(L/'work/gate_integration8.py').write_text(s)
print('Prepared source evidence, documentation checker and applied-tree gate integration.')
