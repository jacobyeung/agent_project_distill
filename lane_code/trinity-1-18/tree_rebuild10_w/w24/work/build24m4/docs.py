from common import *
from storage import growth
iv=J.load(D/'INVARIANTS.json');seals=iv['kits'];up=J.load(L/'out/UPLOADS_24M4.json')
current={r['name']:r for r in J.load(D/'SUITES.json')}
for r in J.load(D/'GUARD_SUITES.json'):current[r['name']]=r
assert all(r['returncode']==0 for r in current.values())
assert all(r['returncode']==0 for r in J.load(D/'EXTRA_SUITES.json'))
J.write(D/'FINAL_SUITES.json',list(current.values())+J.load(D/'EXTRA_SUITES.json'))
checks={}
for p in sorted(D.glob('*TEST*.json')):
 v=J.load(p)
 if 'status' in v:assert v['status']=='PASS',p
 if 'successful' in v:assert v['successful'],p
 if 'failures' in v:assert not v['failures'],p
 if 'errors' in v:assert not v['errors'],p
 checks[p.name]=dict(path=str(p.relative_to(L)),sha256=J.sha(p))
for name in ('q','n','n_go','qd'):
 v=J.load(D/('SCAN_'+name+'.json'));assert v['status']=='PASS' and v['kit_seal']==seals[name]
 checks['SCAN_'+name]=dict(path=str((D/('SCAN_'+name+'.json')).relative_to(L)),sha256=J.sha(D/('SCAN_'+name+'.json')))
shared={rel:{n:J.sha(kit(n)/rel) for n in seals if (kit(n)/rel).exists()} for rel in ('b/z.py','b/resolve.py','b/g.py','b/rg.py','b/rv.py','b/h.py','b/pc.py')}
validation=dict(status='PASS',checks=checks,kits=seals,tree_sha256=iv['tree_sha256'],suite_results='work/build24m4/FINAL_SUITES.json',shared_helper_hashes=shared,storage_compliance='FAIL',
 boundaries=['Complete synthetic source and admitted SQLite stores; actual pinned 320-key pointing list and production room authority in the strict-room cases.',
 'Strict-room census fixtures omit direction_twins; separate fixtures execute the real native Binding constructor, authenticated synthetic twin/alias/union/source pins, real kit classifier and census in all four kits.',
 'Native host fixtures retain their declared synthetic authority, model and capacity boundaries; no production census or launch.',
 'qd shell fixtures substitute prepared stores and host receipts; actual cs.py, h.py, rv.py and decoded shell execute for non-canonical protection and unresolved canonical_scene.',
 'Hidden-path checks use real metadata receipt bytes, declared unavailable-payload stand-ins and a named refusal for the absent catalog; production readiness is not established.'])
J.write(D/'VALIDATION.json',validation)
storage=dict(cap_bytes=100000000,compliance='FAIL',observed_growth_bytes=141709312,peak_continuously_measured=False,reason='Resolver archive copies exceeded the cap before completed evidence was compacted.',current_growth_bytes=growth(),early_setup_allowance_bytes=1048576,lossless_retention=True,no_file_deletion=True)
J.write(D/'STORAGE_LIMIT_BREACH.json',storage)
card=(L/'out/N_CARD_KIT_ROWS.md').read_text();base=J.load(L/'out/DELIVERY_24M3.json')
card=card.replace(base['tree_sha256'],iv['tree_sha256']).replace('(944 files)','(946 files)')
for name,h in base['kits'].items():card=card.replace(h,seals[name])
card=card.replace('UPLOADS_24M3','UPLOADS_24M4').replace('53 files (10571994 bytes) after 24m2d',str(up['total_files'])+' files ('+str(up['total_bytes'])+' bytes) after 24m3').replace('work/build24m3/upload','work/build24m4/upload')
card=card.replace('jd.sh and unchanged dbb2.py are separate files outside the kit seal; their destinations and hashes are in outside_kit_files.','jd.sh and dbb2.py remain unchanged and require no new upload.')
card=card.replace('Tree 24l4r still supplies the post-condition; the planned 24l4s swap remains external.', 'Tree 24l4t supplies the post-condition: either pointing resolution can reveal protection, an unresolvable supplied canonical_scene refuses without a withheld hit, and VQA uses the configured native Binding.room.')
card=card.replace('24l4r has no native producer','The tree has no native producer').replace('DELIVERY_24M3.json','DELIVERY_24M4.json')
card=card.replace('The qd shell fixture proves this continuation with a protected pointing row,', 'The qd shell fixtures prove this continuation with non-canonical pointing protection and an unresolved canonical_scene,')
replace(L/'out/N_CARD_KIT_ROWS.md',card)
lines=[
'Tree '+iv['tree_sha256']+'; '+ '; '.join(n+' '+h for n,h in seals.items())+'.',
'The zero-fuzz patch and all 946 file hashes match TREE24L4T_SEAL.json and the supplied archive (work/build24m4/TREE_VERIFICATION.json).',
'Only source archives, inventories, code pins and dependent seals changed; runtime helpers and config semantics are unchanged (work/build24m4/INVARIANTS.json).',
'Non-canonical pointing protection refuses in q/n/n_go; unresolvable canonical_scene refuses R1_PROTECTED_ROOM_UNRESOLVED:pointing. qd records WOULD_REFUSE (work/build24m4/CENSUS_BYTE_TESTS.json).',
'Both new qd shell cases reach WAITING_REVIEW with bound native census and exact host/receipt publication (work/build24m4/DISCOVERY_CENSUS_SHELL_TESTS.json; DISCOVERY_UNRESOLVED_SHELL_TESTS.json).',
'VQA resolves through native Binding.room in all four kits; clean aliases pass and protected aliases refuse (work/build24m4/VQA_KIT_TESTS.json).',
'Validation passes: 101 native cases, 40 census/host cases, four decoded scans and kit/naming/resolver/guard/live/routing/review-wait suites (work/build24m4/VALIDATION.json; FINAL_SUITES.json).',
'Both hidden-path modes reach the named missing-catalog refusal eac5f9f0 in every kit; production admission remains unproven (work/build24m4/HIDDEN_PATH_TESTS.json).',
f'UPLOADS_24M4.json/.list contain {up["total_files"]} files ({up["total_bytes"]} bytes) after 24m3; the separate GO diff contains three files and is not authorized for upload.',
'GO is false in q/n/qd and true only in the unuploaded n_go template. Existing packages retain their hashes; nothing was uploaded or launched.',
'STORAGE LIMIT BREACH: observed growth reached at least 141,709,312 bytes against the 100,000,000-byte cap; the peak was not continuously measured (work/build24m4/STORAGE_LIMIT_BREACH.json).',
'Completed fixture bytes are retained losslessly under attic; final retained growth is recorded separately in DELIVERY_24M4.json. No deletion command ran.',
'The existing pose-cleanup limitation remains; fixtures establish no production counts (out/REMOVAL_RECEIPTS_BLOCKER.md; work/build24m4/VALIDATION.json).'
]
assert len(lines)<15
(L/'out/BUILD24M4_REPORT.md').write_text('\n'.join(lines)+'\n')
print('Validation, card and 13-line report written')
