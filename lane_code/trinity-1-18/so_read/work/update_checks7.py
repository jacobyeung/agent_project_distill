from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
p=L/'work/run_checks.py';s=p.read_text().replace("('round6','work/src/u0/tests/test_round6.py'),","('round6','work/src/u0/tests/test_round6.py'),\n                  ('round7','work/src/u0/tests/test_round7.py'),")
s=s.replace("('round6_before','test_round6.py','READ_ROUND6_BEFORE','FAILED (failures=31)',[]),", "('round6_before','test_round6.py','READ_ROUND6_BEFORE','FAILED (failures=31)',[]),\n    ('round7_before','test_round7.py','READ_ROUND7_BEFORE','FAILED (failures=10)',[]),")
p.write_text(s)
p=L/'work/build_patches.py';s=p.read_text().replace("'u0/tests/test_round6.py']}","'u0/tests/test_round6.py','u0/tests/test_round7.py']}")
s=s.replace("work/apply-round6","work/apply-round7").replace("('off','round4','round5','round6','compare')", "('off','round4','round5','round6','round7','compare')")
anchor="(L/'out/patches/MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\\n')"
code="""sys.path.insert(0,str(W/'u0'))
from a9 import pack
manifest['kit_files']={p.name:dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
    for p in (L/'out/kit_parity50').iterdir() if p.is_file()}
manifest['kit_files']['sample50.json']['public_sha256']=sha((json.dumps({'u0':pack(json.loads((L/'out/kit_parity50/sample50.json').read_bytes()))},sort_keys=True)+'\\n').encode())
manifest['default_bound_export']=json.loads((L/'out/operations/DEFAULT_EXPORT_PROVENANCE.json').read_text())
"""
s=s.replace(anchor,code+anchor,1)
# The final inventory also retains the derived staged sample digest.
s=s.replace("pins={rel:sha((W/rel).read_bytes()) for rel in sorted(all_files)}", "manifest['kit_files']['sample50.json']['public_sha256']=sha((json.dumps({'u0':pack(json.loads((L/'out/kit_parity50/sample50.json').read_bytes()))},sort_keys=True)+'\\n').encode())\npins={rel:sha((W/rel).read_bytes()) for rel in sorted(all_files)}")
s=s.replace('OFF, round-4/5 integration and comparator suites','OFF, round-4/5/6/7 integration and comparator suites')
p.write_text(s)
p=L/'out/kit_parity50/README.md';s=p.read_text().replace('(four hours), plus one polling interval','(four hours)');p.write_text(s)
p=L/'out/FRAMEWORK_EVIDENCE.md';s=p.read_text().replace('expose name, major/minor capability and total memory','expose name, major/minor capability, multi_processor_count and total memory')
s=s.replace('requires an NVIDIA H100 name, capability 9.0, and 79–86 billion bytes of total memory, which excludes smaller MIG partitions and the 94 GB NVL variant.', 'requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs (`multi_processor_count` at line 12452), capability 9.0, and 79–86 billion bytes of total memory. PCIe, wrong-SM, MIG and NVL variants refuse. The official device-properties page and these installed lines were reread on 2026-11-19 for round 7.')
p.write_text(s)
print('Added round-7 current/baseline/applied suites and updated device source evidence.')
