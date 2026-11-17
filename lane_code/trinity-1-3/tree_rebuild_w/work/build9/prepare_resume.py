"""Retain whole suite-group receipts when every packaged source hash matches."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
p=B/'package.py';s=p.read_text()
start=s.index("    for group in ('generator','legacy','r2'):")
end=s.index("    for group in ('generator','legacy','r2'):",start+1)
s=s[:start]+s[end:]
old="""        empty=Path(tempfile.mkdtemp(prefix='package_empty_',dir=str(L/'work/tmp')))
        assert not any(empty.iterdir())
        (output/'progress.json').write_text(json.dumps(dict(variant=variant,group=group,status='running',cwd=str(empty))))
        with (target/'console.log').open('w') as log:
            result=subprocess.run([sys.executable,'-I','-s','-B',str(root/'work/build9/test_runner.py'),str(target)],
                                  cwd=empty,env=env,stdout=log,stderr=subprocess.STDOUT)
        returncodes.append(result.returncode)
        if result.returncode<0:raise RuntimeError('Test process was killed; stop without retry')
        value=json.loads((target/'results.json').read_text())"""
new="""        checkpoint=target/'GROUP_RECEIPT.json'
        key=dict(source=source_before if variant=='tree' else base_before, fixtures=fixtures_before,
                 runner_sha256=hashlib.sha256((root/'work/build9/test_runner.py').read_bytes()).hexdigest())
        completed=json.loads(checkpoint.read_text()) if checkpoint.exists() else None
        if completed and completed.get('inputs')==key and completed.get('complete'):
            empty=Path(completed['cwd'])
            code=completed['returncode']
            print('Resumed completed group '+variant+'/'+group,flush=True)
        else:
            empty=Path(tempfile.mkdtemp(prefix='package_empty_',dir=str(L/'work/tmp')))
            assert not any(empty.iterdir())
            (output/'progress.json').write_text(json.dumps(dict(variant=variant,group=group,status='running',cwd=str(empty))))
            with (target/'console.log').open('w') as log:
                result=subprocess.run([sys.executable,'-I','-s','-B',str(root/'work/build9/test_runner.py'),str(target)],
                                      cwd=empty,env=env,stdout=log,stderr=subprocess.STDOUT)
            code=result.returncode
            if code<0:raise RuntimeError('Test process was killed; stop without retry')
            value=json.loads((target/'results.json').read_text())
            checkpoint.write_text(json.dumps(dict(inputs=key,complete=value['complete'],returncode=code,cwd=str(empty))))
        returncodes.append(code)
        value=json.loads((target/'results.json').read_text())"""
assert old in s;s=s.replace(old,new).replace("exit_code=result.returncode,cwd=str(empty)","exit_code=code,cwd=str(empty)")
p.write_text(s)
# Delivery construction includes the unchanged comparison inputs and support packet.
s=(B/'make_delivery.py').read_text().replace('tree_rebuild_b6_','tree_rebuild_b8_')
s=s.replace("members.append(B/name)","\n    if (B/name).exists(): members.append(B/name)")
s=s.replace("for row in json.loads((B/'PACKET_INPUTS.json').read_text()):", "for row in json.loads((L/'work/build6/PACKET_INPUTS.json').read_text()):")
(B/'make_delivery.py').write_text(s)
