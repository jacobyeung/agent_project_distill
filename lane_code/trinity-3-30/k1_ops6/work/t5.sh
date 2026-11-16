set -euo pipefail
export TZ=UTC
date -u +%FT%TZ
W=/scratch/jjyeung/orch_n30/k1_ops3/work/partb
B=$W/build; N=$W/build7
P=/scratch/jjyeung/envs/p1cpu/bin/python
df -h /scratch | tail -1
test ! -e $N || { echo "build7 exists"; exit 3; }
mkdir -p $N/evidence/b7_tmp $N/out
cd $B
for f in *; do case "$f" in evidence|rh|out) ;; *) cp -rp "$f" "$N/" ;; esac; done
echo 'eyJhbmNob3JzIjpbMiw0LDYsOCwxMCwxMiwxNCwxNiwxOCwyMCwyMiwyNCwyNiwyOCwzMCwzMl0sImJhc2VfaWRlbnRpdHkiOiJjMjAyMjM2MjM1NzYyZTFjODcxYWQwY2NiNjBjOGVlNWJhMzM3YjlhIiwiY2FtZXJhIjp7ImNhcnJpZXJfdG9rZW4iOiI8fGZpbV9taWRkbGV8PiIsImNvbXBvbmVudF9yZWR1Y3Rpb24iOiJtZWFuIiwiZW1iZWRfZGltIjoyMDQ4LCJmZWF0dXJlX2xheWVyX2NvbnZlbnRpb24iOiJoaWRkZW5fc3RhdGVzX2luZGV4X2tfYWZ0ZXJfa19sYXllcnNfbGFzdF9pc19maW5hbF9ub3JtX3YxIiwiZmVhdHVyZV9sYXllcnMiOm51bGwsImZvdl9hY3RpdmF0aW9uIjoiYm91bmRlZF9zaWdtb2lkX3YxIiwiZnJhbWVfYWRkcmVzc2luZyI6Imdyb3VwMTYiLCJnYXRlIjpudWxsLCJoZWFkX29ubHlfc3RlcHMiOjAsImxtX2dhdGUiOm51bGwsImxvc3NfY2xhbXAiOjEwMC4wLCJtaW5fdHJhamVjdG9yeV9zY2FsZV9tIjowLjA1LCJudW1faGVhZHMiOjE2LCJwbGFjZW1lbnQiOiJhcHBlbmRfYWZ0ZXJfdGVtcG9yYWxfZ3JvdXBfdmlkZW9fdG9rZW5zX3YxIiwicG9pbnRfZGVwdGgiOnsiY29udGV4dF9kZXB0aCI6MiwiZF9wcm9qIjoyNTYsIm1heF9kZXB0aF9tIjoyNS4wLCJtaW5fZGVwdGhfbSI6MC4wNSwibWxwX2hpZGRlbiI6MjU2LCJudW1faGVhZHMiOjgsIm51bV9wb2ludHNfcGVyX2ZyYW1lIjo2NCwic2lsb2dfbGFtYmRhIjowLjUsInNtb290aF9sMV9iZXRhIjowLjEsInZpdF9sYXllcnMiOls5LDE3LDI1XSwid2VpZ2h0IjowLjEsIndlaWdodF9ncmFkIjowLjUsIndlaWdodF9tZXRyaWMiOjAuNSwid2VpZ2h0X3NpbG9nIjoxLjB9LCJwb3NlX2VuY29kaW5nIjoib3BlbmN2X2NhbV9mcm9tX2ZyYW1lMF9hbmNob3Jfc2Vjb25kX29mX3BhaXJfVDNfcXVhdHh5enc0X2Zvdmh3Ml92MiIsInBvc2Vfb3JpZ2luIjoiZmlyc3Rfc2FtcGxlZF9mcmFtZV92MSIsInBvc2VfcmVmZXJlbmNlIjoiZmlyc3RfZ3JvdXBfY29uY2F0X3YxIiwicmVmaW5lX2l0ZXJhdGlvbnMiOjQsInJlcHJlc2VudGF0aXZlX2ZyYW1lIjoic2Vjb25kX29mX3RlbXBvcmFsX3BhaXJfdjEiLCJzdGFnZV9nYW1tYSI6MC42LCJzdXBlcnZpc2lvbiI6eyJwYXRoIjoiL3Byb2plY3QvY29tbXVuaXR5L2pqeWV1bmcvYzdkMzFkZGQvbGIvNTFmMDEzMTM5ZTc3Lm5weiIsInNoYTI1NiI6IjUxZjAxMzEzOWU3NzViZjFmMGFkYWRhYzZhOGY1OTczZDAxOTcxN2ZmY2E4MDA2OThkODFiNzQ5ODAzMTJjMDQifSwidG9rZW5fc2NoZW1lIjoiZmlyc3RfYW5kX3Jlc3RfbGVhcm5lZF92MSIsInRyYWplY3RvcnlfYmFsYW5jZSI6ZmFsc2UsInRydW5rX2RlcHRoIjo0LCJ3YXJtdXBfcmF0aW8iOjAuMCwid2VpZ2h0IjowLjIsIndlaWdodF9mb2NhbCI6MC41LCJ3ZWlnaHRfZ3Jhdml0eSI6MC4xLCJ3ZWlnaHRfcm90IjoxLjAsIndlaWdodF9zY2FsZSI6MC4wNCwid2VpZ2h0X3RyYW5zIjoxLjB9LCJkZXB0aF9jb252ZW50aW9uIjoib3B0aWNhbF9heGlzX21ldHJpYyIsImRpbWVuc2lvbnMiOnsibGFuZ3VhZ2UiOjQwOTYsInZpc2lvbiI6MTE1Mn0sImVuY29kZXJfY29weSI6eyJjb21wdXRlX2R0eXBlIjoiYmZsb2F0MTYiLCJrZXlfcHJlZml4IjoiIiwicGFyYW1ldGVyX2R0eXBlIjoiZmxvYXQzMiIsInRlbnNvcl9zaGEyNTYiOiI3NmE1YmE0ZDU5YTBhY2VhM2IyOTAzZDQ2ZTExYjNmZDE1Y2JmNGY2OTViZThiZjIwYzMxZWZjNzU1NTM0MzJjIiwid2VpZ2h0cyI6eyJwYXRoIjoiL3NjcmF0Y2gvZnN3L3BvcnRmb2xpb3MvYXYvcHJvamVjdHMvYXZfZGF0YWVuZ2luZV9jb3QvdXNlcnMvanlldW5nL2FwLzk3YTZhM2ViL3J1bnMvYjE5YzEyMDAvdHJhaW4vc3RlcF80MDAvZW5jb2Rlci5zYWZldGVuc29ycyIsInNoYTI1NiI6IjA0ODIzNTkwODg2NjU3NzUwMTRjYjQ2YzEwZjZkODdhNmY5OWM0MjAzYTk3OGI2YjZkMWE3NGE1MDE1NTQzOGQifX0sImZlYXR1cmVfYmFja2luZyI6ImRlY291cGxlZF92YyIsImZlYXR1cmVfZHR5cGUiOiJiZmxvYXQxNiIsImZlYXR1cmVfZW5jb2Rlcl9zaGEyNTYiOiI2N2E0NmZlNDY5MTg1ZjQxY2MzMTM1NDQyMzM5OTJkYzJjMThmYjViZDNjNmE4YWJiYWIwOGQ3MGY4Y2IyNzcwIiwiaGVhZF9kdHlwZSI6ImZsb2F0MzIiLCJoZWFkX2xvc3Nfd2VpZ2h0IjowLjAsInByb3ZlbmFuY2UiOnsiYmFzZSI6eyJwYXRoIjoiL3NjcmF0Y2gvZnN3L3BvcnRmb2xpb3MvYXYvcHJvamVjdHMvYXZfZGF0YWVuZ2luZV9jb3QvdXNlcnMvanlldW5nL2FwL2ZjYTNiMWVkL2FybS9mcm96ZW4vNDc4ZDAxNDAvbW9kZWwuanNvbiIsInNoYTI1NiI6ImNjNzI0ZDVlZTFiMGJkNjJiYTc1OWJlM2ViMDgzMWFmZDAwOWNkNzYzNWVhNTk2NmRkYzBmZDI2YzQ1OTlmYjcifSwiY29uZmlnX3NoYTI1NiI6IjQ1ZDIxZGQyZWQ1MzE0YjM1NmVhZDU5YTQzYjg4NTBmMjJhYTM4MjkxNmJlMjQyZmQ1NzkxMmRiMjkzYjMzZjQiLCJwcmVwYXJhdGlvbiI6eyJwYXRoIjoiL2x1c3RyZS9mc3cvcG9ydGZvbGlvcy9hdi9wcm9qZWN0cy9hdl9kYXRhZW5naW5lX2NvdC91c2Vycy9qeWV1bmcvYXAvOTdhNmEzZWIvYXJtL2Zyb3plbi9iMTlhMTIwMC9yZWNlaXB0Lmpzb24iLCJzaGEyNTYiOiJhNjBmM2E5ZjcyYmVlYjQ5ZTFjYzdlZTA0OTc5MDNiYjAwMDQ1OGE3ZmFmOTliNzZkOWUwYmMxNmE4YzE1MzdiIn0sInJlY2lwZSI6eyJlbmNvZGVyX2xlYXJuaW5nX3JhdGUiOjFlLTA1LCJnbG9iYWxfYmF0Y2giOjY0LCJsZWFybmluZ19yYXRlIjowLjAwMDEsIm1pbGVzdG9uZXMiOlsyMDAsNDAwLDgwMCwxMjAwXSwic2VlZCI6MTcsInN0ZXBzIjoxMjAwLCJ3YXJtdXBfcmF0aW8iOjAuMDMsIndlaWdodF9kZWNheSI6MC4wMSwid29ybGRfc2l6ZSI6OH0sInN0YXJ0Ijp7InBhdGgiOiIvc2NyYXRjaC9mc3cvcG9ydGZvbGlvcy9hdi9wcm9qZWN0cy9hdl9kYXRhZW5naW5lX2NvdC91c2Vycy9qeWV1bmcvYXAvZmNhM2IxZWQvYXJtL2Zyb3plbi80NzhkMDE0MC9tb2RlbC5qc29uIiwic2hhMjU2IjoiY2M3MjRkNWVlMWIwYmQ2MmJhNzU5YmUzZWIwODMxYWZkMDA5Y2Q3NjM1ZWE1OTY2ZGRjMGZkMjZjNDU5OWZiNyJ9fSwic2NoZW1hIjoicDMtaGVhZC1hcnRpZmFjdC12MSIsInN0YXJ0IjoiYmFzZSIsInN0ZXAiOjQwMCwidGVtcG9yYWxfZ3JvdXBpbmciOiJmdXNlZF9wYWlyc19zZWNvbmRfYW5jaG9yIiwidHJhbnNsYXRpb25fY29udmVudGlvbiI6Im1ldHJpYyIsIndlaWdodHMiOnsicGF0aCI6Ii9zY3JhdGNoL2Zzdy9wb3J0Zm9saW9zL2F2L3Byb2plY3RzL2F2X2RhdGFlbmdpbmVfY290L3VzZXJzL2p5ZXVuZy9hcC85N2E2YTNlYi9ydW5zL2IxOWMxMjAwL3RyYWluL3N0ZXBfNDAwL2hlYWRzLnNhZmV0ZW5zb3JzIiwic2hhMjU2IjoiMDdjMmQzYjAzNThmZDZmMTZlMDE0ZjRhMTU1YmVlNmRlOTIxZTY3MjNhNWI5NjMzZDA4ZDBmYjcxZThmYWQzOSJ9fQo=' | base64 -d > $N/inputs/depth_heads.json
sha256sum $N/inputs/depth_heads.json
cd $N
stat -c '%h %n' stage_job.py rh_batch_fixture.py
$P -B - <<'PY'
from pathlib import Path
import os
p = Path('stage_job.py'); assert os.stat(p).st_nlink == 1
t = p.read_text()
anchor = "    NS.verify_inventory({k:v['sha256'] for k,v in inventory.items()}, model['files'])\n"
assert t.count(anchor) == 1
add = ("    # The prepared config's Stage-1 depth init and the two files it pins (native_stage.py:470-473).\n"
       "    for index, item in enumerate(assets['depth']):\n"
       "        target = NS.physical(root, item['logical_path'])\n"
       "        target.parent.mkdir(parents=True, exist_ok=True)\n"
       "        records['depth_' + str(index)] = NS.copied(item, target)\n")
p.write_text(t.replace(anchor, anchor + add))
q = Path('rh_batch_fixture.py'); assert os.stat(q).st_nlink == 1
t = q.read_text()
anchor1 = "    # Transport keys are always production names/paths. Fixture identities remain\n"
assert t.count(anchor1) == 1
add1 = ("    # Depth assets: heads.json travels as its real bytes (production verifier runs);\n"
        "    # the two weight files are labelled stand-ins (production verifier NOT exercised).\n"
        "    real_heads = package / 'inputs/depth_heads.json'\n"
        "    depth = []\n"
        "    for index, item in enumerate(a['depth']):\n"
        "        if index == 0 and real_heads.is_file() and H.sha(real_heads) == item['sha256']:\n"
        "            depth.append(dict(item, path=str(real_heads)))\n"
        "            continue\n"
        "        path = objects / ('depth_' + str(index))\n"
        "        path.write_bytes(('RH depth stand-in ' + str(index) + '\\n').encode())\n"
        "        depth.append(dict(item, path=str(path), bytes=path.stat().st_size, sha256=H.sha(path)))\n"
        "    a['depth'] = depth\n")
t = t.replace(anchor1, add1 + anchor1)
anchor2 = "+ list(zip(config['export']['parts'], c['export']['parts'])):\n"
assert t.count(anchor2) == 1
t = t.replace(anchor2, "+ list(zip(config['export']['parts'], c['export']['parts'])) + list(zip(config['assets']['depth'], a['depth'])):\n")
q.write_text(t)
print('patched')
PY
diff -u $B/stage_job.py stage_job.py > evidence/B7_STAGE_JOB.diff || true
diff -u $B/rh_batch_fixture.py rh_batch_fixture.py > evidence/B7_FIXTURE.diff || true
cat evidence/B7_STAGE_JOB.diff
cat evidence/B7_FIXTURE.diff
$P -B -c "import ast;ast.parse(open('stage_job.py').read());ast.parse(open('rh_batch_fixture.py').read());print('syntax ok')"
cp -p packet/CONFIG.json evidence/B7_CONFIG_before.json
cp -p packet/a7e31d84.sh evidence/B7_batch_before.sh
nice -n 19 $P -B build_package.py > evidence/B7_BUILD.log 2>&1; echo build_rc=$?
cat evidence/B7_BUILD.log
cmp packet/CONFIG.json evidence/B7_CONFIG_before.json && echo CONFIG_IDENTICAL
sha256sum packet/a7e31d84.sh $B/packet/a7e31d84.sh packet/CONFIG.json $B/packet/CONFIG.json packet/d6e92a81.tar
ls -la packet/
echo "--- bwrap"; ls -la /usr/bin/bwrap 2>&1; /usr/bin/bwrap --ro-bind / / /bin/true && echo BWRAP_OK || echo BWRAP_FAIL
