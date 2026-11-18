from pathlib import Path
W=Path(__file__).resolve().parent
helper='''
def check_bundle_guard(package, root):
    """Exercise the embedded batch layout through the installed process guard."""
    import ast
    import io
    batch = (package/'BATCH.sh').read_text()
    lines = [line for line in batch.splitlines() if line.startswith('b=bytes.fromhex(')]
    if len(lines) != 1:
        raise ValueError('Bundle encoding differs')
    expression = ast.parse(lines[0]).body[0].value
    if (not isinstance(expression, ast.Call) or ast.unparse(expression.func) != 'bytes.fromhex'
            or len(expression.args) != 1 or expression.keywords):
        raise ValueError('Bundle encoding differs')
    raw = bytes.fromhex(ast.literal_eval(expression.args[0]))
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        members = archive.getmembers()
        if len(members) != 3 or {m.name for m in members} != {'0.py', '0.json', '7.py'}:
            raise ValueError('Bundle inventory differs')
        for member in members:
            if not member.isfile():
                raise ValueError('Unsafe bundle member')
            with (root/member.name).open('xb') as stream:
                stream.write(archive.extractfile(member).read())
    if json.loads((root/'0.json').read_text()) != json.loads((package/'0.json').read_text()):
        raise ValueError('Bundle descriptor differs')
    expected = (package/'a/6.py').read_bytes()
    if (root/'7.py').read_bytes() != expected:
        raise ValueError('Bundled operator differs')
    vendor = root/'bootstrap/orchard_h10/vendor/return_io.py'
    subprocess.run([sys.executable, '-I', '-s', '-B', str(vendor), '--help'],
                   env={'PATH': '/usr/bin:/bin', 'CUDA_VISIBLE_DEVICES': ''},
                   capture_output=True, check=True)
    if (root/'6.py').read_bytes() != vendor.read_bytes():
        raise ValueError('Process guard did not exercise its write target')
    if (root/'7.py').read_bytes() != expected:
        raise ValueError('Process guard changed bundled operator')
    return dict(passed=True, operator_sha256=hashlib.sha256(expected).hexdigest(),
                batch_sha256=hashlib.sha256(batch.encode()).hexdigest(),
                path='7.py', guard_target='6.py', action='--help')

'''
for label in ('b1','b2'):
 d=W/label
 p=d/'tower_bootstrap.py';s=p.read_text().replace("root/'6.py'","root/'7.py'")
 s=s.replace("proof['passed'] is True", "proof['passed'] is True and proof.get('bundle_guard_passed') is True")
 s=s.replace("  argv=[*argv[:-2]", "  if sha(root/'7.py')!=operator_sha256:\n   raise ValueError('Bundled operator changed after startup')\n  argv=[*argv[:-2]")
 p.write_text(s)
 p=d/'node_check.py';s=p.read_text().replace('\ndef main():',helper+'\ndef main():')
 s=s.replace('    install_process_guard(root)\n', '    install_process_guard(root)\n    bundle_guard=check_bundle_guard(package,root)\n')
 s=s.replace("dict(passed=True,", "dict(passed=True,bundle_guard_passed=True,bundle_guard=bundle_guard,",1 if label=='b1' else 1)
 p.write_text(s)
 p=d/'build_operator.py';s=p.read_text().replace("'6.py':(O/'tower_sequence.py')", "'7.py':(O/'tower_sequence.py')")
 # Preserve the complete reviewed read plan, changing identity and CPU admission metadata only.
 start=s.index("write(O/'READ_PLAN.json'")
 end=s.index('\nprint(',start)
 s=s[:start]+'''plan=json.loads((O/'original/READ_PLAN.json').read_text())
plan.update(token=public['token'],plan_sha256=public['plan_sha256'],
            operator_sha256=sha(O/'tower_sequence.py'),operator_path='7.py')
plan['cpu_check']={**plan.get('cpu_check',{}), 'partition':'preempt', 'cpus':8,
    'memory':'200G','walltime':'04:00:00','gpus':0,'exclude':'orchard-flame-[0-31]',
    'results':'a/c/CPU.json','required_flags':['passed','bundle_guard_passed']+
        (['full_reader_passed','full_reader.passed'] if 'full_reader_passed' in (O/'node_check.py').read_text() else []),
    'helper_sha256':sha(O/'node_check.py'),'bootstrap_sha256':sha(O/'tower_bootstrap.py')}
write(O/'READ_PLAN.json',plan)
(O/'PACKAGE.json').write_bytes((P/'PACKAGE.json').read_bytes())
''' + s[end:]
 p.write_text(s)
