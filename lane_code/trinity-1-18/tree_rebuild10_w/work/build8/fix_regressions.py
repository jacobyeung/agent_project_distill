"""Supply the inputs required by current contracts without changing assertions."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]; T=L/'work/tree_r1'; B=L/'work/build8'
for p in B.glob('*.py'):
    if p.name in ('bootstrap.py','fix_regressions.py'):continue
    raw=p.read_text(); p.write_text(raw.replace('tests.test_r2_build8','tests.test_r2_build7'))
def edit(name,old,new):
    p=T/name;s=p.read_text();assert s.count(old)==1,(name,old);p.write_text(s.replace(old,new))
edit('tests/test_carrier_c1_run.py',"('authenticate', 'fixture'), ('processor_for', SimpleNamespace()),",
     "('authenticate', 'fixture'), ('processor_for', SimpleNamespace(tokenizer=SimpleNamespace())),")
edit('tests/test_r2_build5_edges.py',"result=make(dict(input=dict(path='u/new',sha256='0'*64)),{},base)",
     "unknown=make(dict(input=dict(path='u/unknown',sha256='0'*64)),{},base)\n        self.assertEqual(unknown['entries']['u/unknown']['required_parameter'],'artifact_'+'0'*64)\n        # A parts entry now requires a registered source pin. Planning reads metadata only.\n        pin='7cc01f3655130e9d7ef2c1fd597c5cd7c1ddbcb49314a4dce7aecc040ec88cba'\n        result=make(dict(input=dict(path='u/new',sha256=pin)),{},base)")
edit('tests/test_r2_build5_host_order.py',"write(root/'plan.json',dict(entries=entries,venv=dict(sha256='a'*64),bwrap=dict(sha256='b'*64)))",
     "runtime=dict(file=str(executable),sha256=file_pin(executable)['sha256'])\n    write(root/'plan.json',dict(entries=entries,venv=runtime,bwrap=runtime))")
edit('tests/test_r2_build5_host_order.py',"stdlib_version=[3,6],venv_sha256='a'*64,bwrap_sha256='b'*64,",
     "stdlib_version=[3,6],venv_sha256=runtime['sha256'],bwrap_sha256=runtime['sha256'],")
