from common import *
v=J.load(D/'VALIDATION.json');assert v['status']=='PASS'
i=J.load(D/'INVARIANTS.json');up=J.load(L/'out/UPLOADS_24M4J.json')
# Keep unexpected validation outputs verbatim. Required negative fixtures are
# recorded separately in PROBE_TESTS and the native guard records.
logs=[]
for p in (L/'attic/build24m4j').rglob('*.log'):
 if p.name in ('missing.log','shadow.log'):continue
 raw=p.read_text(errors='replace')
 if 'Traceback (most recent call last)' in raw or 'ENV_UNRESOLVED:' in raw:
  logs.append(dict(path=str(p.relative_to(L)),output=raw))
J.write(D/'FAILURES.json',dict(scope='Unexpected validation failures retained with exact output; final checks pass',records=logs,setup_outputs=[dict(action='Initial shell heredoc',output="/bin/bash: -c: line 44: syntax error near unexpected token `('\n/bin/bash: -c: line 44: `s=s[:s.index(\"def input_file\")]+'''def input_file(h):'\n"),dict(action='Original-archive assumption',output='AssertionError: local work/build24m4h/p.tar does not hash to e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536; its e7c9a966 archive was reconstructed. Exact extracted file inventory authentication passed.'),dict(action='Optional network namespace',output='bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted\n')],cluster_kill=False,final_validation='work/build24m4k/VALIDATION.json'))
lines=[
 '; '.join(n+' '+h for n,h in i['kits'].items())+'; kit_n_go k/c.json payload sha256 '+i['n_go_payload_sha256']+'; identity '+i['n_go_identity']+'.',
 'Tree C remains '+i['tree_sha256']+'; rb.py bytes match across all four kits.',
 'The child probes 75 imports across 67 P modules; direct third-party roots are PIL, numpy, scipy, tokenizers, torch and transformers. IMPORT_AUDIT.md records lazy paths, environment pins and version limits.',
 'The child binds the parent interpreter, sites and overlays read-only, puts P first, disables site hooks, and refuses missing imports or top-level shadowing by name before build().',
 'P’s file inventory matches b83a8a35 and all 204 implementation entries; original archive e5be8157 is required on Orchard. Selection 5db993b1 and the complete 4e8e6c04 database-hash gate remain unchanged.',
 'The real bwrap probe, missing-module and shadow fixtures, read-only mount tests, both full-hash refusals, native rb/rg/pl checks and all 16 scan/kit/naming/resolver/guard/arming suites pass.',
 'The arming helper declares the 24m4i q/n baseline, includes cumulative kit changes and all four required configuration capsules, and passes complete delta replay.',
 'rcj/rcj.sh and rcj/x.py total 19106 bytes: preempt, 16 CPUs, 128 GB, two hours, no GPU/requeue; 65 authenticated recipe/source pins plus runtime assets, with no checkpoint weights or frame payloads.',
 'The CPU job probes and reconstructs through rb.py, then publishes native receipts, materialization, whole-file DB hash/size/header, probe results and timings independently before propagating failures; transport and publication fixtures pass.',
 '173626 staged for 1184 s; 226 s preceded frame/init staging. Reduced staging is estimated at 3–6 min; RCJ_USAGE.md gives the submit command and outputs. No Orchard job was submitted.',
 f'UPLOADS_24M4J.json/.list contain {up["total_files"]} files ({up["total_bytes"]} bytes): q/n against 24m4i, qd against 24m4h 62d8a7f5 including its unapplied 24m4i delta. GO is false except kit_n_go; GO delta is separate.',
 'Production rows and processor assets are unavailable locally; the full production database was not rebuilt. Local probe versions are not claimed as Orchard versions.',
 'work/build24m4k/FAILURES.json retains failure output; VALIDATION.json records final checks. Tests expose only w24j as writable and block superseded-workspace imports; no SSH, network, Git, GPU, scheduler or other-agent work ran.',
 'DELIVERY_24M4J.json and PACKAGE_CHECK.json record the full archive, checksum, member verification, preserved input members and storage below 25 GB.'
]
assert len(lines)<15
(L/'out/BUILD24M4J_REPORT.md').write_text('\n'.join(lines)+'\n')
# Keep supplied versions distinct from archive-level pinning.
p=D/'IMPORT_AUDIT.md';s=p.read_text().replace('not individually pinned in the supplied kit metadata','no individual version string in the supplied kit metadata');replace(p,s)
print('REPORT',len(lines),'lines; retained unexpected outputs',len(logs))
