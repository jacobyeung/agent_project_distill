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

The pool probe writes and fsyncs 131,072 random bytes, verifies their SHA256, and reserves 131,104 bytes including the ledger write. Both CPU guards in `a/5.py` and the pre-submission receipt check `a/9.py` read `WRITE_TEST_BYTES` from the sealed pool writer `orchard_h10/vendor/return_io.py`; the guards also verify the retained file, receipt hash, ledger charge and guarded helper. The cumulative pool and metadata budgets remain unchanged.

The CPU check of `a38bd627f901e` failed because the build changed only one side of a constant. The previous `revision8.py:49` replaced `4*1024**2` with `131072` in `return_io.py`, so the guarded write test wrote 128 KiB, while `a/5.py:53` (`out/WT_OLD_5.py:53`, from `inspect/a_5.py:49`) still required 4 MiB and raised at line 54. The mismatch was deterministic; no job ID, node, time, path, token or sibling placement entered it. The receipt is not written by placement: each CPU check creates a fresh `wpool/<token>/.wtest` under its own job-local temporary root through `orchard_results.write_test` and the guarded `return_io.py test` subprocess, then compares it at once. The second guard (`out/WT_OLD_5.py:77`) and `a/9.py:23`, which `o_check_sub.sh` runs on `CPU.json` before the GPU submit, pinned the same stale 4 MiB and would have failed next. Local tests missed all three because they called the operator directly, stopped at boot, or fed `a/9.py` no real CPU receipt.

`tests/test_write_receipt.py` runs the delivered `BATCH.sh` CPU route with job IDs that differ from 173995, a fresh pool, and three spent sibling placements, then runs `a/9.py` on the resulting `CPU.json` as `o_check_sub.sh` does. Remote staging and model execution use tiny fixtures; the pool writer, reservation ledger, guarded subprocess, bootstrap dispatch, receipt check and authenticated fetch are real. The old `a/5.py` and the old `a/9.py` line both reject the new receipt. Wrong receipt sizes, changed evidence sizes or hashes, exhausted budgets, changed settings and later preparation failures all fail with bounded diagnostics.

`a/30.json` records the CPU failure, the failed check's name, and up to 16 comparisons, with each expected/found value bounded to 2,048 characters. Supervisor recovery returns the matching job/plan record as `metadata/30.json`, alongside boot status and the traceback. When the exception follows a passed comparison, `failed_check` is null and `comparison_status` says so. A failed pool subprocess records its expected and actual exit status and bounded stderr. A failed `a/9.py` size check prints the expected and found sizes.

`tests/test_vpy.py` separately checks all 411 imports through the real pinned archives, production capture and namespace argv. The host bwrap executable, scratch bindings and sleeping watcher helper are substituted. New fixtures remain in the approved sibling directory; no files are deleted.

Token `{b['token']}` supersedes the placed tokens `a6f198d3c7b20`, `a7e29d4c8f103` and `a38bd627f901e` and the unplaced interim build `ad07f53341bc0`; placement and submission use fresh paths and one-use locks.

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
 for previous in ('a38bd627f901e','ad07f53341bc0'):s=s.replace(previous,b['token'])
 s=re.sub(r'\b(?:73|75|76|84) tests\b','85 tests',s)
 s=re.sub(r'Delivery SHA256: `[0-9a-f]{64}`\.', 'Delivery SHA256: `'+b['delivery_sha256']+'`.',s)
 s=re.sub(r'Token: `[^`]+`\. Delivery: `out/delivery.tgz`, \*\*[\d,]+ bytes\*\*\.\nSHA256: `[0-9a-f]{64}`\.',f"Token: `{b['token']}`. Delivery: `out/delivery.tgz`, **{b['delivery_bytes']:,} bytes**.\nSHA256: `{b['delivery_sha256']}`.",s)
 for key,value in rows.items():s=re.sub(r'\| '+re.escape(key)+r' \| [\d,]+ \|','| '+key+' | '+format(value,',')+' |',s)
 s=marker+'\n'+paragraph+end+'\n\n'+s;p.write_text(s)
