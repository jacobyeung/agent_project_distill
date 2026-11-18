"""Verify both deliveries and publish the entry-sequence seal audit."""
from pathlib import Path
import ast,copy,hashlib,io,json,subprocess,sys,tarfile

W=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def archive(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        members=tar.getmembers()
        assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
        assert len({m.name for m in members})==len(members)
        return {m.name:tar.extractfile(m).read() for m in members}

for label,doc in [('b1','OPERATIONS_TOWER.md'),('b2','OPERATIONS_ROOM.md')]:
    d=W/label;baseline=json.loads((d/'FOLLOWUP_BASE.json').read_text())
    token=(d/'TOKEN').read_text().strip()
    delivery=archive((d/'1.tgz').read_bytes());payload=archive(delivery['0.tgz'])
    line=next(s for s in delivery['BATCH.sh'].decode().splitlines() if s.startswith('b=bytes.fromhex('))
    bundle=archive(bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0])))
    manifest=json.loads(delivery['PACKAGE.json']);public=json.loads(delivery['0.json'])
    plan=json.loads((d/'READ_PLAN.json').read_text())
    assert token==public['token']==manifest['token']==plan['token']
    assert set(bundle)=={'0.py','0.json','7.py'}
    assert bundle['7.py']==delivery['a/6.py']==(d/'tower_sequence.py').read_bytes()
    assert sha(bundle['7.py'])==baseline['tower_sequence.py']==plan['operator_sha256']
    assert bundle['0.py']==(d/'tower_bootstrap.py').read_bytes()
    assert bundle['0.json']==delivery['0.json']
    assert delivery['a/5.py']==(d/'node_check.py').read_bytes()
    assert sha(delivery['0.tgz'])==baseline['0.tgz']==public['payload_sha256']
    assert delivery['0.tgz']==(d/'0.tgz').read_bytes()
    assert (d/'PACKAGE.json').read_bytes()==delivery['PACKAGE.json']
    assert len(delivery['0.tgz'])==public['payload_bytes']
    assert set(delivery)=={str(p.relative_to(d/'package')) for p in (d/'package').rglob('*') if p.is_file()}
    for name,raw in delivery.items():assert raw==(d/'package'/name).read_bytes(),name
    for name,h in manifest['files'].items():assert sha(delivery[name])==h,name
    cfg=json.loads(payload['9.json'])
    assert sha(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode())==public['plan_sha256']
    for name,pin in cfg['payload_pins'].items():assert dict(bytes=len(payload[name]),sha256=sha(payload[name]))==pin
    for name in ('a/1.json','a/export.json'):assert sha(delivery[name])==baseline['package/'+name]
    check=plan['cpu_check']
    assert check['partition']=='preempt' and check['cpus']==8 and check['memory']=='200G'
    assert check['walltime']=='04:00:00' and check['exclude']=='orchard-flame-[0-31]'
    assert check['helper_sha256']==sha(delivery['a/5.py'])
    assert check['bootstrap_sha256']==sha(bundle['0.py'])
    assert 'entry_sequence_passed' in check['required_flags']
    for path in [*d.glob('commands_*.sh'),d/'sub2']:
        subprocess.run(['bash','-n',str(path)],check=True)
        text=path.read_text()
        if "<<'PYCODE'" in text:ast.parse(text.split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0])
    local=json.loads((d/'LOCAL_ENTRY_CHECK.json').read_text())
    cpu=local['cpu'];result=Path(local['results'])
    assert cpu==json.loads((result/'CPU.json').read_text())
    assert cpu['entry_sequence_passed'] is True
    assert cpu['entry_sequence']['events']==['guard_installed','write_test','operator_dispatch']
    root=Path(cpu['root']);entry=cpu['entry_sequence']
    evidence=root/'wpool'/token/'.wtest'
    assert evidence.stat().st_size==entry['write_test']['bytes']==4194304
    assert sha(evidence.read_bytes())==entry['write_test']['sha256']
    assert sha((root/'7.py').read_bytes())==entry['operator_sha256_before']==entry['operator_sha256_after']
    assert sha((root/'6.py').read_bytes())==entry['guard_target_sha256']
    assert json.loads((root/'a/1.json').read_text())['action']==1
    # Verify the actual operator-created outputs, not a separately invoked rehearsal.
    output=Path(json.loads((root/'a/1.json').read_text())['config']['output'])
    assert json.loads((output/'metadata/MEMORY.json').read_text())==cpu['memory']
    rehearsal=json.loads((output/'REHEARSAL.json').read_text())
    if label=='b2':assert rehearsal[0]['full_reader']==cpu['full_reader']
    verify=d/'verify'
    for name,raw in delivery.items():
        path=verify/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    (verify/'a/c').mkdir(exist_ok=True)
    for name in ('CPU.json','MEMORY.json')+(('FULL_READER.json',) if label=='b2' else ()):
        (verify/'a/c'/name).write_bytes((result/name).read_bytes())
    code=plan['commands']['cpu_pass_check'].split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0]
    def check_proof(value):
        (verify/'a/c/CPU.json').write_text(json.dumps(value))
        return subprocess.run([sys.executable,'-I','-B','-c',code,str(verify)],capture_output=True,text=True)
    success=check_proof(cpu);assert success.returncode==0,success.stderr
    mutations={
        'flag_false':lambda c:c.update(entry_sequence_passed=False),
        'flag_missing':lambda c:c.pop('entry_sequence_passed'),
        'order':lambda c:c['entry_sequence'].update(events=['guard_installed','operator_dispatch','write_test']),
        'collision':lambda c:c['entry_sequence']['dispatched_argv'].__setitem__(-2,str(root/'6.py')),
        'write_bytes':lambda c:c['entry_sequence']['write_test'].update(bytes=0),
        'write_sha':lambda c:c['entry_sequence']['write_test'].update(sha256='bad'),
        'guard_sha':lambda c:c['entry_sequence'].update(guard_target_sha256='0'*64),
        'operator_sha':lambda c:c['entry_sequence'].update(operator_sha256_after='0'*64),
        'shared_pool':lambda c:c['entry_sequence'].update(pool='/project/community/jjyeung/okh7/ae71c903')}
    for name,mutate in mutations.items():
        value=copy.deepcopy(cpu);mutate(value)
        assert check_proof(value).returncode!=0,name
    (verify/'a/c/CPU.json').write_bytes((result/'CPU.json').read_bytes())
    suites={p.name:json.loads(p.read_text()) for p in sorted(d.glob('tests_*result.json'))}
    counts={k:sum(s[k] for s in suites.values()) for k in ('tests','failures','errors','skipped')}
    assert counts['failures']==counts['errors']==counts['skipped']==0
    hashes={name:sha((d/name).read_bytes()) for name in ('0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json')}
    validation=dict(token=token,hashes=hashes,operator_sha256=plan['operator_sha256'],tests=counts,suites=suites,
        payload_members=len(payload),changed_payload_members=[],unchanged_operator=True,unchanged_inputs=True,
        delivery_verified=True,commands_parsed=7,documented_pass_check=success.stdout.strip(),
        pass_check_negative_cases=list(mutations),entry_sequence_local_proof=str(result/'CPU.json'),
        orchard_cpu_check=False,gpu_execution=False)
    write(d/'FINAL_VERIFICATION.json',validation)
    write(d/'TEST_SUMMARY.json',counts)
    lines=[f'Token: {token}',f"Final results: {counts['tests']} passed, 0 failed, 0 errors, 0 skipped.",
        'CPU Python: /scratch/jjyeung/envs/p1cpu/bin/python. All runs use at most eight CPU threads.',
        'Package, constraints, sequence, memory and guard suites passed; b2 also passed the CPU-helper suite.',
        'Both local entry proofs run the actual bundled bootstrap wrapper and operator subprocess.',
        'Allocation, namespace, storage proof, stage, restore, local paths and Python are explicit fixtures.',
        'The write test is real: 4 MiB under the fixture root/wpool, through the installed Popen guard.',
        'The operator subprocess creates MEMORY.json; b2 also creates both full-reader CPU records.',
        'Order, guard-target collision, operator mutation and missing/false/nonboolean entry flags fail closed.',
        'Seven command scripts parse; the documented pass check accepts each local receipt and rejects nine corruptions.',
        'Local receipts do not replace the required allocated Orchard CPU check.','']
    for name,r in suites.items():lines.append(f"{name}: {r['tests']} passed, {r['failures']} failed, {r['errors']} errors, {r['skipped']} skipped.")
    lines+=['','Commands from W7:']
    for name,file in [('package','tests/test_package.py'),('constraints','tests/test_constraints.py'),('sequence','work/test_sequence.py'),('memory','work/test_operator_memory.py')]+([('cpu_helper','work/test_cpu_helper.py')] if label=='b2' else []):
        lines.append(f'PATH=/usr/bin:/bin OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B run_suite.py {label}/{file} {label}/tests_{name}_result.json')
    lines.append(f'PATH=/usr/bin:/bin OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 /scratch/jjyeung/envs/p1cpu/bin/python -B bundle_regression.py {label}')
    lines+=['','Tests retain their fixtures. Budget disk space before rerunning them.']
    (d/'TESTS.txt').write_text('\n'.join(lines)+'\n')
    report=f'''Package `{token}` requires `entry_sequence_passed=true` before GPU launch. The CPU check installs the process guard, stages its inputs, extracts the actual BATCH.sh bundle, and calls the production `orchard_results.write_test` against `root/wpool`. It verifies the retained 4 MiB file and confirms that the guard wrote `root/6.py` while `root/7.py` kept its sealed hash.

The CPU helper imports `make_dispatch` from the extracted `root/0.py`. It passes an action-1 config with `device=cpu`, `measure_memory=True`, and `rehearsal=True`, using argv ending in `root/a/5.py root/a/1.json`. The bootstrap rewrites the operator path to `root/7.py` and re-hashes it immediately before launching. The unchanged operator already accepts this config. Production admission, argv rewriting and dispatch checks retain their behavior; admission additionally requires the entry-sequence flag.

CPU.json binds the write-test bytes and SHA256, the guard-target SHA256, the operator SHA256 before and after execution, and both requested and dispatched argv. The operator subprocess produces MEMORY.json. The room operator also produces the dev-S1 and R0-dev full-reader records with explicit model stubs. Any failed entry step prevents a passing receipt.

The final suites passed {counts['tests']} tests with zero failures, errors or skips. Both local entry proofs execute the real guarded write test, bundled bootstrap wrapper and operator subprocess. Allocation, namespace, storage, staging, restore and local path/Python adaptation remain fixtures. The local proof does not establish Orchard staging or real model quality. LOCAL_ENTRY_CHECK.json and LOCAL_REHEARSAL.json identify the executed roots and receipts. The documented pass check accepts these receipts and rejects nine corruptions; TESTS.txt lists exact suite commands.

The token, every 0.tgz payload byte, operator bytes, input descriptors, read settings, item lists, walltimes and margins are unchanged from the W7 baseline in FOLLOWUP_BASE.json. The bootstrap, CPU helper, embedded bundle, package manifest and delivery are resealed. FILE_SHA256_DIFF.tsv lists changed file hashes against that baseline. This explicit baseline comparison is retained because the requested seal audit requires it.

Orchard's allocated CPU check and GPU evaluation remain pending. The local pool test does not test the shared return pool's capacity. Staging availability, shared-pool capacity and b1's five-hour partial-run estimate remain external risks. The operator re-hash does not eliminate the interval between checking a path and the child opening it. No SSH, Git, network, job submission, GPU execution or process termination ran here.

The authoritative outputs are 0.tgz, 1.tgz, PACKAGE.json, READ_PLAN.json, TESTS.txt, FINAL_VERIFICATION.json, LOCAL_ENTRY_CHECK.json and {doc}. The `sub2` script duplicates the full CPU pass check in `commands_2.sh`. These command scripts are operator instructions; they were parsed locally, not submitted.

'''
    report+='\n'.join(f'`{name}` SHA256: `{value}`' for name,value in hashes.items())+'\n'
    report+=f"\nOperator SHA256: `{plan['operator_sha256']}`\n\n"+(d/doc).read_text()
    (d/'REPORT.md').write_text(report)
    current={name:sha((d/name).read_bytes()) for name in baseline if (d/name).is_file()}
    for name in ('sub2','LOCAL_ENTRY_CHECK.json','LOCAL_REHEARSAL.json','FINAL_VERIFICATION.json'):
        current[name]=sha((d/name).read_bytes())
    reasons={'tower_bootstrap.py':'Importable dispatch wrapper; require entry_sequence_passed; preserve re-hash.',
        'node_check.py':'Run real guarded pool write test and bundled bootstrap dispatch; bind entry evidence.',
        'build_operator.py':'Require entry_sequence_passed in CPU-check metadata.',
        'package/BATCH.sh':'Embed the importable bootstrap and strict entry-sequence gate.',
        'package/a/5.py':'Sealed CPU helper executes the real entry sequence.',
        '1.tgz':'Rebuilt delivery with authenticated helper and bootstrap.',
        'PACKAGE.json':'Update embedded bundle and CPU helper hashes.',
        'package/PACKAGE.json':'Update embedded bundle and CPU helper hashes.',
        'READ_PLAN.json':'Bind CPU helper/bootstrap hashes, required flag and exact operating commands.'}
    changes=[dict(path=name,old_sha256=baseline.get(name,'-'),new_sha256=h,
        reason=reasons.get(name,'Current entry-sequence evidence, validation results and operating commands.'))
        for name,h in sorted(current.items()) if h!=baseline.get(name)]
    write(d/'FILE_SHA256_DIFF.json',dict(baseline='FOLLOWUP_BASE.json',token=token,token_changed=False,
        payload_changed=False,operator_changed=False,changes=changes))
    (d/'FILE_SHA256_DIFF.tsv').write_text('path\told_sha256\tnew_sha256\treason\n'+
        '\n'.join('\t'.join(str(row[k]) for k in ('path','old_sha256','new_sha256','reason')) for row in changes)+'\n')
    print(label,counts,hashes,flush=True)
