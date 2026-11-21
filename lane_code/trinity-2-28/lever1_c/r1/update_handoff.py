"""Render the current delivery identity and boot contract in both handoffs."""
import json,re
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build_depth as B
b=json.loads((HERE/'out/BUILD.json').read_text());boot=b['boot']
public={k:v for k,v in b.items() if k not in ('layout','external_inputs','forecast','boot','boot_closure')}
descriptor=len(B.B.jd(public))
paragraph=f"""The boot gate imports all {len(b['boot_closure']['modules'])} audited modules before staging any checkpoint, weight or frame. It stages CPython from runtime group 0, the base environment from group 1, `v/py` and its overlay from input 3, and policy from input 4. Pre-bulk authenticated source bytes total **{boot['pre_bulk_bytes']:,}**, including **{boot['package_archive_bytes']:,}** package bytes. Runtime group 0's other members and all bulk inputs follow a successful boot receipt.

The pool probe writes and fsyncs 131,072 random bytes, verifies their SHA256, and reserves 131,104 bytes including the ledger write. Both CPU guards read `WRITE_TEST_BYTES` from the sealed pool writer and verify the retained file, receipt, ledger and guarded helper. The cumulative pool and metadata budgets remain unchanged.

`out/WT_OLD_5.py:53` and `:77` preserve the two stale 4 MiB expectations from the placed CPU entry. `revision8.py:49` had reduced the writer to 128 KiB. The first comparison failed deterministically after staging; no job ID, node, time, token or previous placement changed its expected size. The CPU check creates its own fresh `root/wpool/token/.wtest` through `orchard_results.write_test`, the guarded subprocess and `return_io.operate('test')`. It does not compare against a placement-time receipt. Existing tests invoked the operator directly or stopped at boot, so they never exercised this pair of guards.

`tests/test_write_receipt.py` runs the delivered BATCH CPU route and both guards with different job IDs, fresh state and three spent sibling placements. Remote staging and model execution use tiny fixtures; the pool writer, reservation ledger, guarded subprocess, bootstrap dispatch and authenticated fetch are real. The old entry reproduces the mismatch. Wrong receipt sizes, changed evidence sizes or hashes, exhausted budgets, changed settings and later preparation failures all fail with bounded diagnostics.

`a/30.json` records the CPU failure and up to 16 comparisons, with each expected/found value bounded to 2,048 characters. Supervisor recovery returns the matching job/plan record as `metadata/30.json`, alongside boot status and the traceback. A later CPU failure retains the successful write-test comparison. A failed pool subprocess records its expected and actual exit status and bounded stderr.

`tests/test_vpy.py` separately checks all 411 imports through the real pinned archives, production capture and namespace argv. The host bwrap executable, scratch bindings and sleeping watcher helper are substituted. New fixtures remain in the approved sibling directory; no files are deleted.

Token `{b['token']}` supersedes the placed tokens `a6f198d3c7b20`, `a7e29d4c8f103` and `a38bd627f901e`; placement and submission use fresh paths and one-use locks.

"""
proof_path=HERE/'out/VPY_CHECKS.json'
if proof_path.exists():
 proof=json.loads(proof_path.read_text())
 if proof.get('passed') and proof.get('delivery_sha256')==b['delivery_sha256']:
  paragraph+=f"The real-archive production-capture boot passed: {proof['boot']['modules']} modules, child and worker exit codes 0, zero bulk bytes, and {len(proof['path_audit']['links']):,} resolved symlinks. Local pre-bulk staging took {proof['stage_seconds']:.2f} seconds and boot launch took {proof['boot']['launch_seconds']:.2f} seconds.\n\n"
rows={'`out/delivery.tgz`':b['delivery_bytes'],'Expanded inner payload (32 MiB limit)':b['payload_expanded_bytes'],
      'Installed package files':b['installed_bytes'],'Installed `BUILD.json`':descriptor,
      'Streamed `orchard/o_place.sh`':(HERE/'orchard/o_place.sh').stat().st_size,
      'Conservative delivery + installed files + descriptor':b['delivery_bytes']+b['installed_bytes']+descriptor}
for name in ('PLACE.md','REPORT.md'):
 p=HERE/name;s=p.read_text()
 marker='<!-- boot-order -->';end='<!-- /boot-order -->'
 if marker in s:s=s[:s.index(marker)]+s[s.index(end)+len(end):].lstrip('\n')
 s=s.replace('a38bd627f901e',b['token'])
 s=re.sub(r'\b(?:73|75|76) tests\b','84 tests',s)
 s=re.sub(r'Delivery SHA256: `[0-9a-f]{64}`\.', 'Delivery SHA256: `'+b['delivery_sha256']+'`.',s)
 s=re.sub(r'Token: `[^`]+`\. Delivery: `out/delivery.tgz`, \*\*[\d,]+ bytes\*\*\.\nSHA256: `[0-9a-f]{64}`\.',f"Token: `{b['token']}`. Delivery: `out/delivery.tgz`, **{b['delivery_bytes']:,} bytes**.\nSHA256: `{b['delivery_sha256']}`.",s)
 for key,value in rows.items():s=re.sub(r'\| '+re.escape(key)+r' \| [\d,]+ \|','| '+key+' | '+format(value,',')+' |',s)
 s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
