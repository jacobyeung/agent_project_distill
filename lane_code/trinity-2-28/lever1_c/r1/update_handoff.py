"""Keep delivery identity and boot accounting consistent in the handoff."""
import json,re
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build_depth as B
b=json.loads((HERE/'out/BUILD.json').read_text());boot=b['boot']
public={k:v for k,v in b.items() if k not in ('layout','external_inputs','forecast','boot','boot_closure')}
descriptor=len(B.B.jd(public))
p=HERE/'PLACE.md';s=p.read_text()
s=re.sub(r'Delivery SHA256: `[0-9a-f]{64}`\.', 'Delivery SHA256: `'+b['delivery_sha256']+'`.',s)
rows={'`out/delivery.tgz`':b['delivery_bytes'],'Expanded inner payload (32 MiB limit)':b['payload_expanded_bytes'],
      'Installed package files':b['installed_bytes'],'Installed `BUILD.json`':descriptor,
      'Streamed `orchard/o_place.sh`':(HERE/'orchard/o_place.sh').stat().st_size,
      'Conservative delivery + installed files + descriptor':b['delivery_bytes']+b['installed_bytes']+descriptor}
for key,value in rows.items():s=re.sub(r'\| '+re.escape(key)+r' \| [\d,]+ \|','| '+key+' | '+format(value,',')+' |',s)
s=s.replace('67 tests','72 tests').replace('71 tests','72 tests').replace('all 334 Python files','all 335 Python files').replace('all 344 delivered','all 345 delivered')
s=s.replace('The shared environment, step-544 carrier/private-head weights, tower weights, processor assets, and their authentication remain up front. They are required to compute the first served scale.', 'The shared environment and full worker import closure precede every checkpoint, weight, processor and frame extraction. Those bulk inputs follow only a successful boot receipt; they are required to compute the first served scale.')
s=s.replace('It authenticates the existing shared archives once, indexes RGB offsets without extracting those frames, and materializes only capture 1.', 'It authenticates runtime inputs before the worker import gate, then stages the bulk archives, indexes RGB offsets without extracting those frames, and materializes only capture 1. The mixed environment archive is authenticated as a filtered stream before boot and copied again after boot for its remaining members.')
marker='<!-- boot-order -->';end='<!-- /boot-order -->'
if marker in s:s=s[:s.index(marker)]+s[s.index(end)+len(end):].lstrip('\n')
timing='Production pre-bulk seconds are unmeasured (`null` in BUILD.json and FORECAST.json); `metadata/25.json` records staging, launch, closure and total pre-bulk seconds for each job.'
checks=json.loads((HERE/'out/PREBULK_CHECKS.json').read_text()) if (HERE/'out/PREBULK_CHECKS.json').exists() else {}
if checks.get('delivery_sha256')==b['delivery_sha256']:
    rows=checks['cases'];timing+=' Local missing-module regressions measured '+', '.join(f"{r['case'].removeprefix('boot_').upper()} {r['boot']['pre_bulk_seconds']:.3f} s ({r['boot']['pre_bulk_bytes']:,} fixture bytes)" for r in rows)+'. Both staged zero bulk bytes and returned the cause through production fetch.'
paragraph=f'''Both CPU and GPU jobs now stage package code and runtime inputs, boot numeric worker action 3 in the production interpreter and namespace, import all {len(b['boot_closure']['modules'])} audited modules and verify {len(b['boot_closure']['symbols']):,} imported symbols, write a boot receipt, and only then stage checkpoints, weights and frames. `boot_order.py:39` inserts the gate into the shared `job.stage`; `runtime/boot.py:46` launches the worker with the production environment builder, vnice prefix, cache root and working directory. `metadata/25.json` records success or failure; failures retain the traceback in the authenticated production return.

Pre-bulk source bytes total **{boot['pre_bulk_bytes']:,}**: package archive **{boot['package_archive_bytes']:,}**, pinned template runtime/interpreter archives **{boot['runtime_archive_bytes']:,}**, environment/policy streams **{boot['environment_policy_stream_bytes']:,}**, and bwrap **{boot['bwrap_bytes']:,}**. These are authenticated input bytes, not expanded disk usage. The mixed environment stream materializes only `v/` and `q/`; it stores no checkpoint or frame member before boot. Its remaining members are staged after success. The existing 600-second staging allowance includes the boot gate and remains unmeasured.

{timing} The local regression substitutes runtime archives, interpreter binding and namespace mounts; it exercises the delivered worker entry, loader, environment construction, working directory, staging gate and fetch. The full closure check rejects the local p1cpu environment because it lacks torchvision; no successful full closure run in the Orchard environment or live GPU timing is claimed.

'''
s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
p=HERE/'REPORT.md';s=p.read_text()
s=re.sub(r'Token: `[^`]+`\. Delivery: `out/delivery.tgz`, \*\*[\d,]+ bytes\*\*\.\nSHA256: `[0-9a-f]{64}`\.',f"Token: `{b['token']}`. Delivery: `out/delivery.tgz`, **{b['delivery_bytes']:,} bytes**.\nSHA256: `{b['delivery_sha256']}`.",s)
s=s.replace('all 67 tests','all 72 tests').replace('all 71 tests','all 72 tests')
if marker in s:s=s[:s.index(marker)]+s[s.index(end)+len(end):].lstrip('\n')
s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
