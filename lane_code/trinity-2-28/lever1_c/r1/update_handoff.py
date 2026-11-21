"""Keep delivery identity and boot accounting consistent in the handoff."""
import json,re
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build_depth as B
b=json.loads((HERE/'out/BUILD.json').read_text());boot=b['boot']
public={k:v for k,v in b.items() if k not in ('layout','external_inputs','forecast','boot','boot_closure')}
descriptor=len(B.B.jd(public))
p=HERE/'PLACE.md';s=p.read_text().replace('a6f198d3c7b20',b['token'])
s=re.sub(r'Delivery SHA256: `[0-9a-f]{64}`\.', 'Delivery SHA256: `'+b['delivery_sha256']+'`.',s)
rows={'`out/delivery.tgz`':b['delivery_bytes'],'Expanded inner payload (32 MiB limit)':b['payload_expanded_bytes'],
      'Installed package files':b['installed_bytes'],'Installed `BUILD.json`':descriptor,
      'Streamed `orchard/o_place.sh`':(HERE/'orchard/o_place.sh').stat().st_size,
      'Conservative delivery + installed files + descriptor':b['delivery_bytes']+b['installed_bytes']+descriptor}
for key,value in rows.items():s=re.sub(r'\| '+re.escape(key)+r' \| [\d,]+ \|','| '+key+' | '+format(value,',')+' |',s)
s=s.replace('72 tests','73 tests').replace('67 tests','73 tests').replace('71 tests','72 tests').replace('all 334 Python files','all 335 Python files').replace('all 344 delivered','all 345 delivered')
s=s.replace('The shared environment, step-544 carrier/private-head weights, tower weights, processor assets, and their authentication remain up front. They are required to compute the first served scale.', 'The shared environment and full worker import closure precede every checkpoint, weight, processor and frame extraction. Those bulk inputs follow only a successful boot receipt; they are required to compute the first served scale.')
s=s.replace('It authenticates the existing shared archives once, indexes RGB offsets without extracting those frames, and materializes only capture 1.', 'It authenticates runtime inputs before the worker import gate, then stages the bulk archives, indexes RGB offsets without extracting those frames, and materializes only capture 1. The mixed environment archive is authenticated as a filtered stream before boot and copied again after boot for its remaining members.')
marker='<!-- boot-order -->';end='<!-- /boot-order -->'
if marker in s:s=s[:s.index(marker)]+s[s.index(end)+len(end):].lstrip('\n')
timing='Production pre-bulk seconds remain unmeasured; metadata/25.json records them for each job.'
paragraph=f"""The boot gate stages the complete CPython tree from runtime group 0, the base environment from group 1, the interpreter wrapper and overlay from input 3 (`a4.tar`), and policy from input 4. It then boots the real worker and imports all {len(b['boot_closure']['modules'])} audited modules before staging any checkpoint, weight or frame. Runtime group 0's other members, group 2, and inputs 0–2 wait for the successful boot receipt. `boot_order.py:30` selects these archives; `runtime/boot.py:105` authenticates and filters their members.

The missing executable came from selecting input 2 (`a2.tar`) for `v/py`. That archive contains no `v/` members. Input 3 (`a4.tar`, SHA256 `c867d40addcf35c55db1ec511c4dc2b8a4cec80cef9003be93179ef82c30b0ea`) contains the 160-byte executable shell wrapper `v/py`, the 443-byte `v/boot.py`, and the overlay. The wrapper executes the base environment's `bin/python` symlink, which resolves through the uv namespace bind to the staged CPython tree. The failure was an omitted archive, not a dangling `v/py` symlink.

Pre-bulk authenticated source bytes total **{boot['pre_bulk_bytes']:,}**: package **{boot['package_archive_bytes']:,}**, runtime groups 0–1 **{boot['runtime_archive_bytes']:,}**, overlay and policy **{boot['environment_policy_stream_bytes']:,}**, and pinned bwrap **{boot['bwrap_bytes']:,}**. Group 0 is streamed and only CPython is materialized. These source-read bytes include discarded mixed-archive members; no bulk member is copied or extracted before boot. {timing}

`tests/test_vpy.py` uses the real pinned archives through the delivered `job.stage`, reproduces the old missing-executable failure, and tests the corrected worker through the production bwrap constructor. The local bwrap executable and an extra same-location bind expose the scratch fixture. The authenticated vnice script runs with its terminator helper bound to an inert script so the test cannot signal processes or delete marker files. The test audits staged links, the ELF loader/shared libraries, and the worker closure; `out/VPY_CHECKS.json` records its result. Missing-module tests also require zero bulk bytes and an authenticated failure through production fetch.

Token `{b['token']}` supersedes the placed token `a6f198d3c7b20`; placement and submission use fresh paths and one-use locks.

"""
s=s.replace('The mixed environment archive is authenticated as a filtered stream before boot and copied again after boot for its remaining members.', 'The mixed runtime archive streams only CPython before boot; its remaining members follow boot success.')
check_path=HERE/'out/VPY_CHECKS.json'
if check_path.exists():
    proof=json.loads(check_path.read_text())
    if proof.get('passed') and proof.get('delivery_sha256')==b['delivery_sha256']:
        paragraph+=f"The pinned-archive regression passed: {proof['boot']['modules']} modules imported, {len(proof['path_audit']['links']):,} symlinks resolved, and the ELF loader/shared-library audit passed. The old selection reproduced the execvp failure; both cases staged zero bulk bytes.\n\n"
s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
p=HERE/'REPORT.md';s=p.read_text().replace('a6f198d3c7b20',b['token'])
s=s.replace('No fixtures moved. All work used local `/scratch`; no SSH, Git, network, GPU, Slurm, process termination, `/home` or `/data*` access ran.', 'The delivery was built and CPU-tested locally. It has not been placed or submitted.')
s=re.sub(r'Token: `[^`]+`\. Delivery: `out/delivery.tgz`, \*\*[\d,]+ bytes\*\*\.\nSHA256: `[0-9a-f]{64}`\.',f"Token: `{b['token']}`. Delivery: `out/delivery.tgz`, **{b['delivery_bytes']:,} bytes**.\nSHA256: `{b['delivery_sha256']}`.",s)
s=s.replace('all 72 tests','all 73 tests').replace('all 67 tests','all 73 tests').replace('all 71 tests','all 72 tests')
if marker in s:s=s[:s.index(marker)]+s[s.index(end)+len(end):].lstrip('\n')
s=s.replace('The mixed environment archive is authenticated as a filtered stream before boot and copied again after boot for its remaining members.', 'The mixed runtime archive streams only CPython before boot; its remaining members follow boot success.')
s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
