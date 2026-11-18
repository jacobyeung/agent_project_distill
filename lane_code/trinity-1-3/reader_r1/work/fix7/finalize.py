from pathlib import Path
import ast,hashlib,io,json,subprocess,tarfile
W=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def archive(raw):
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:
  members=t.getmembers()
  assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
  assert len({m.name for m in members})==len(members)
  return {m.name:t.extractfile(m).read() for m in members}
def bundle(raw):
 line=next(s for s in raw.decode().splitlines() if s.startswith('b=bytes.fromhex('))
 return archive(bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0])))
for label,old,doc in [('b1','b1g','OPERATIONS_TOWER.md'),('b2','b2r','OPERATIONS_ROOM.md')]:
 d=W/label;s=W.parent/old/'out';token=(d/'TOKEN').read_text().strip()
 delivery=archive((d/'1.tgz').read_bytes());payload=archive(delivery['0.tgz']);oldpayload=archive((s/'0.tgz').read_bytes())
 b=bundle(delivery['BATCH.sh']);oldbundle=bundle((s/'package/BATCH.sh').read_bytes())
 manifest=json.loads(delivery['PACKAGE.json']);public=json.loads(delivery['0.json'])
 assert token==public['token']==manifest['token']
 assert len(token)==13 and token[0] in 'abcdef' and all(c in '0123456789abcdef' for c in token)
 assert set(b)=={'0.py','0.json','7.py'}
 assert b['7.py']==delivery['a/6.py']==(d/'tower_sequence.py').read_bytes()==(s/'tower_sequence.py').read_bytes()
 assert b['0.py']==(d/'tower_bootstrap.py').read_bytes() and b['0.json']==delivery['0.json']
 assert delivery['a/5.py']==(d/'node_check.py').read_bytes()
 assert (d/'PACKAGE.json').read_bytes()==delivery['PACKAGE.json']
 assert set(delivery)=={str(p.relative_to(d/'package')) for p in (d/'package').rglob('*') if p.is_file()}
 for name,raw in delivery.items():assert raw==(d/'package'/name).read_bytes(),name
 for name,h in manifest['files'].items():assert sha(delivery[name])==h,name
 assert sha(delivery['0.tgz'])==public['payload_sha256'] and len(delivery['0.tgz'])==public['payload_bytes']
 cfg=json.loads(payload['9.json']);prior=json.loads(oldpayload['9.json']);prior['token']=token;assert cfg==prior
 assert sha(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode())==public['plan_sha256']
 assert set(payload)==set(oldpayload)
 assert [n for n in payload if payload[n]!=oldpayload[n]]==['9.json']
 for name,pin in cfg['payload_pins'].items():assert dict(bytes=len(payload[name]),sha256=sha(payload[name]))==pin
 plan=json.loads((d/'READ_PLAN.json').read_text());oldplan=json.loads((s/'READ_PLAN.json').read_text())
 for name in ('sequence','expected','arms','modes','rules','read_settings','memo_scope','save_own_depth','walltime','stop_margin','return_margin'):
  assert plan[name]==oldplan[name],name
 for name in ('inputs_tower.json','export_544.json'):
  assert (d/name).read_bytes()==(s/name).read_bytes()
 assert delivery['a/1.json']==(s/'package/a/1.json').read_bytes()
 assert delivery['a/export.json']==(s/'package/a/export.json').read_bytes()
 check=plan['cpu_check'];assert check['partition']=='preempt' and check['cpus']==8 and check['memory']=='200G' and check['walltime']=='04:00:00' and check['exclude']=='orchard-flame-[0-31]'
 for p in d.glob('commands_*.sh'):
  subprocess.run(['bash','-n',str(p)],check=True)
  text=p.read_text()
  if "<<'PYCODE'" in text:ast.parse(text.split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0])
 # Execute the documented pass checker against a locally assembled delivery and a labelled fixture receipt.
 verify=d/'verify';verify.mkdir(exist_ok=True)
 for name,raw in delivery.items():
  p=verify/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 cpupath=Path(json.loads((d/'GUARD_receipt.json').read_text())['cpu'])
 (verify/'a/c').mkdir(exist_ok=True)
 for name in ('CPU.json','MEMORY.json')+ (('FULL_READER.json',) if label=='b2' else ()):
  (verify/'a/c'/name).write_bytes((cpupath.parent/name).read_bytes())
 code=plan['commands']['cpu_pass_check'].split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0]
 r=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-B','-c',code,str(verify)],check=True,capture_output=True,text=True)
 suites={p.name:json.loads(p.read_text()) for p in sorted(d.glob('tests_*result.json'))}
 counts={key:sum(v[key] for v in suites.values()) for key in ('tests','failures','errors','skipped')}
 assert counts['failures']==counts['errors']==counts['skipped']==0
 hashes={name:sha((d/name).read_bytes()) for name in ('0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json')}
 validation=dict(token=token,hashes=hashes,tests=counts,suites=suites,payload_members=len(payload),
                 changed_payload_members=['9.json'],unchanged_operator=True,unchanged_inputs=True,
                 delivery_verified=True,commands_parsed=6,documented_pass_check=r.stdout.strip(),
                 orchard_cpu_check=False,gpu_execution=False)
 (d/'FINAL_VERIFICATION.json').write_text(json.dumps(validation,indent=2)+'\n')
 lines=[f'Token: {token}',f"Final results: {counts['tests']} passed, 0 failed, 0 errors, 0 skipped.",
        'Python: /scratch/jjyeung/envs/p1cpu/bin/python; at most 8 CPU threads; all fixtures retained in W7.',
        'Existing tests/ files are unchanged. run_suite.py redirects only b2 historical fixture roots to read-only W5.',
        'Additional sequence tests expect 7.py and use a real startup digest; memory tests supply the required bundle flag.',
        'The room CPU helper uses the real guard; its storage, staging and restore remain explicit local fixtures.',
        'Local suite runs do not replace the allocated Orchard CPU check.', '']
 for name,r in suites.items():lines.append(f"{name}: {r['tests']} passed, {r['failures']} failed, {r['errors']} errors, {r['skipped']} skipped.")
 lines+=['','Commands (run from W7):']
 for name in ('package','constraints','sequence','memory')+ (('cpu_helper',) if label=='b2' else ()):
  file={'package':'tests/test_package.py','constraints':'tests/test_constraints.py','sequence':'work/test_sequence.py','memory':'work/test_operator_memory.py','cpu_helper':'work/test_cpu_helper.py'}[name]
  lines.append(f'OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B run_suite.py {label}/{file} {label}/tests_{name}_result.json')
 lines.append(f'OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B bundle_regression.py {label}')
 lines+=['','Regression coverage: old overwrite; new bundle survival; exact dispatch digest; nested entry guard; mutation refusal;',
         'missing/false/nonboolean CPU flag refusal; tampered operator refusal; missing guard write refusal;',
         'CPU failure publishes no receipt; success publishes a bound flag; token-only payload change.',
         'Final archive validation and six command blocks also passed; these checks are not counted as unit tests.']
 (d/'TESTS.txt').write_text('\n'.join(lines)+'\n')
 report=f'''Package `{token}` launches the sealed operator from `root/7.py`. The process guard may overwrite `root/6.py` and `root/a/6.py`; neither path holds the production launch operator. The bootstrap requires `bundle_guard_passed=true` and verifies the startup operator digest immediately before dispatch. A mismatch raises `ValueError` and never calls the allocation runner.

The empty-root helper decodes the actual BATCH.sh bundle after installing the guard, runs the real vendor helper with `--help`, verifies the guard wrote its target, and compares the bundled operator with the delivered `a/6.py`. CPU.json records the bundle and operator hashes. Any check failure prevents a passing receipt. The room package also requires its full-reader stub pass.

The final test run passed {counts['tests']} tests with zero failures, errors, or skips. The existing tests/ suites remain byte-identical. The additional sequence and memory fixtures reflect the new filename and required flag. See TESTS.txt for exact local commands and per-suite counts. The room CPU-helper tests retain the full-reader stub pass, using existing local image fixtures and explicit staging/restore stubs.

The payload differs from `{(s/'TOKEN').read_text().strip()}` only in the token field of `9.json`. All other {len(payload)-1} payload members, both input descriptors, the operator, read settings, item lists, walltimes and margins are unchanged. The payload digest and canonical plan digest change because they authenticate that token. FILE_SHA256_DIFF.tsv gives old/new SHA256 values and reasons for each changed sealed member and copied build source. This explicit comparison is retained because the requested seal audit requires it.

The selected filename and all inspected write destinations are documented in ../WRITE_PATH_AUDIT.md. Pinned external template archives are unavailable for a complete local member inventory. Their extractor uses exclusive creation, so a collision with the bundled operator fails staging instead of overwriting it. The dispatch re-hash refuses any other pre-launch change. It does not remove the inherent interval between checking a path and the child opening it.

No Orchard staging, allocated CPU check, GPU evaluation, network transfer, or job submission ran here. The allocated check remains required. Package 1 retains its five-hour partial-run estimate; the shared return pool capacity and staging availability remain external risks. A local fixture receipt must not be used as the Orchard receipt.

Authoritative outputs are 0.tgz, 1.tgz, PACKAGE.json, READ_PLAN.json, TESTS.txt, FINAL_VERIFICATION.json, this report and {doc}. Other copied evidence files describe the source package and serve existing tests.

'''
 report+='\n'.join(f'`{name}` SHA256: `{h}`' for name,h in hashes.items())+'\n\n'
 report+='The following operator instructions contain the exact placement, metadata, preempt CPU, pass-check, submission, fetch, unpack and scoring commands.\n\n'+(d/doc).read_text()
 (d/'REPORT.md').write_text(report)
 # Scope every sealed payload, decoded bundle and delivery member; include copied build sources/docs/tests.
 olddelivery=archive((s/'1.tgz').read_bytes())
 rows=[]
 def compare(scope,a,b,reason):
  for n in sorted(a.keys()|b.keys()):
   av=a.get(n);bv=b.get(n)
   if av!=bv:rows.append((scope,n,sha(av) if av is not None else '-',sha(bv) if bv is not None else '-',reason(n)))
 compare('payload',oldpayload,payload,lambda n:'Fresh token in 9.json; every other plan field and payload byte is preserved.')
 compare('bundle',oldbundle,b,lambda n:{'0.py':'Use 7.py; require CPU bundle flag; re-hash before dispatch.','0.json':'Token, payload size/hash and canonical plan hash authenticate the new seal.','6.py':'Moved unchanged operator bytes to 7.py to avoid the guard target.','7.py':'Same operator bytes formerly bundled as 6.py; unused runtime path.'}[n])
 reasons={'0.tgz':'Fresh token changes only payload member 9.json.','1.tgz':'Delivery wraps the resealed descriptor, bundle and CPU helper.',
   '0.json':'Token and derived payload/plan hashes.','CONFIG.json':'Token and derived payload/plan hashes.',
   'BATCH.sh':'Bundle operator at 7.py with dispatch re-hash and CPU gate.',
   'PACKAGE.json':'New token and hashes for changed sealed files.',
   'a/5.py':'CPU helper tests actual embedded bundle through real process guard.',
   'tower_bootstrap.py':'Use 7.py, require CPU flag, and re-hash immediately before dispatch.',
   'node_check.py':'Exercise real bundle and harmless guard write; publish bound bundle flag.',
   'build_package.py':'Preserve the complete source payload; reseal only its plan token.',
   'build_operator.py':'Bundle 7.py and retain reviewed read plan with updated CPU metadata.',
   'TOKEN':'Fresh opaque 13-hex namespace.',
   'src/9.json':'Synchronize extracted plan with token-only resealed payload.',
   'READ_PLAN.json':'New seal identity, bundle guard requirements and exact operator commands.',
   'REPORT.md':'Current results, seal hashes, scope, risks and exact operator commands.',
   'TESTS.txt':'Current test counts, scope and reproducible local commands.',
   doc:'New token and hashes; preempt sbatch, all CPU flags and W7 scoring paths.',
   'BUILD.json':'Token-only reseal inventory and canonical plan digest.',
   'FINAL_VERIFICATION.json':'Final seal, payload-preservation and command validation evidence.',
   'CPU_HELPER_TEST.json':'CPU helper regression now exercises the real process guard.'}
 compare('delivery',olddelivery,delivery,lambda n:reasons[n])
 files=['0.tgz','1.tgz','PACKAGE.json','src/9.json','tower_bootstrap.py','node_check.py','build_package.py','build_operator.py','TOKEN','READ_PLAN.json','REPORT.md','TESTS.txt',doc,'BUILD.json','FINAL_VERIFICATION.json']
 if label=='b2':files.append('CPU_HELPER_TEST.json')
 compare('workspace',{n:(s/n).read_bytes() for n in files if (s/n).exists()},{n:(d/n).read_bytes() for n in files},lambda n:reasons[n])
 for name in ('test_sequence.py','test_operator_memory.py','test_memo.py')+(('test_cpu_helper.py',) if label=='b2' else ()):
  a=(s.parent/'work'/name).read_bytes();z=(d/'work'/name).read_bytes()
  if a!=z:rows.append(('test','work/'+name,sha(a),sha(z),'Relocate fixtures into W7; update 7.py/digest and CPU-flag expectations; CPU helper keeps the real guard.'))
 (d/'FILE_SHA256_DIFF.tsv').write_text('scope\tpath\told_sha256\tnew_sha256\treason\n'+'\n'.join('\t'.join(r) for r in rows)+'\n')
 (d/'FILE_SHA256_DIFF.json').write_text(json.dumps(dict(old_token=(s/'TOKEN').read_text().strip(),new_token=token,
    scope='Every changed sealed payload, decoded bundle and delivery member, plus changed copied build sources, required documents and selected test fixtures. New local logs and fixture trees are not delivery members.',
    changes=[dict(zip(('scope','path','old_sha256','new_sha256','reason'),r)) for r in rows]),indent=2)+'\n')
 print(label,counts,hashes)
