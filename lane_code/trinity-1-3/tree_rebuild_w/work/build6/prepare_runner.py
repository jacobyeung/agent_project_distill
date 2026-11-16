from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build6';P=L/'work/contracts_r6'
s=(P/'run_tests_r6.py').read_text()
s=s.replace("L=Path(__file__).resolve().parents[1]", "L=Path(__file__).resolve().parents[2]")
s=s.replace("tree=L/'work/base/work/base/tree_b01ce449' if sys.argv[1]=='overlay' else L/'work/trees'/sys.argv[1]", "tree=L/'work/tree_r1'")
s=s.replace("L/'work/tests_r6'", "L/'work/contracts_r6/tests_r6'").replace("L/'out/PATCH_MANIFEST_R6.json'", "L/'work/contracts_r6/PATCH_MANIFEST_R6.json'")
s=s.replace("root=L/'work/tmp'/tag", "root=L/'work/tmp/packet_r6'\nproof=L/'work/build6/proofs/packet'\nproof.mkdir(parents=True,exist_ok=True)")
s=s.replace("L/f'work/{tag}_results.json'", "proof/'results.json'").replace("L/f'work/{tag}_trace.json'", "proof/'trace.json'")
# Keep packet assertions, collection, timeouts and retained fixtures. Add the
# lane's existing boundary census and completed-product compaction.
s=s.replace('import pytest', "sys.path.insert(0,str(L/'work/build5'))\nfrom compact_tmp import inventory, compact\nsizes=[]\nimport pytest")
s=s.replace('        self.current=item.nodeid\n', "        measured=sum(inventory(L/'work/tmp').values())\n        sizes.append(dict(test=item.nodeid,phase='before',bytes=measured))\n        if measured>200*1024**2:raise RuntimeError('temporary storage policy')\n        self.current=item.nodeid\n")
s=s.replace('        signal.alarm(0)\n', "        signal.alarm(0)\n        measured=sum(inventory(L/'work/tmp').values())\n        sizes.append(dict(test=item.nodeid,phase='after',bytes=measured))\n        compact(root)\n        if measured>200*1024**2:raise RuntimeError('temporary storage policy')\n")
s=s.replace('raise SystemExit(result)', "(proof/'temporary_sizes.json').write_text(json.dumps(sizes,indent=2))\nraise SystemExit(result)")
(B/'packet_runner.py').write_text(s)
before=(P/'run_tests_r6.py').read_text()
import difflib
(B/'PACKET_RUNNER.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='packet runner',tofile='lane runner')))
print('Runner paths adapted; boundary size checks added. Assertions unchanged.')
