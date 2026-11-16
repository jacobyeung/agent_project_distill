"""Relocate the supplied tests and use efficient stdlib statement monitoring."""
import difflib, json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';source=L/'work/contracts_r6/tests_r6';tests=B/'packet/tests_r6';proof=B/'proofs/packet'
tests.mkdir(parents=True,exist_ok=True);(proof/'work/test_artifacts_r6').mkdir(parents=True,exist_ok=True)
edits=[]
for p in source.iterdir():
    if not p.is_file():continue
    if p.suffix=='.py':
        old=p.read_text();new=old.replace('L=Path(__file__).resolve().parents[2]',"L=Path(__file__).resolve().parents[2]/'proofs/packet'")
        new=new.replace("L/'work/base/work/base/tree_b01ce449/student_pilot/sam3_tower.py'", "Path(__file__).resolve().parents[4]/'work/base/tree_b01ce449/student_pilot/sam3_tower.py'")
        (tests/p.name).write_text(new)
        if old!=new:edits.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=p.name,tofile=p.name)))
    else:(tests/p.name).write_bytes(p.read_bytes())
s=(B/'packet_runner.py').read_text()
s=s.replace("L/'work/contracts_r6/tests_r6'", "L/'work/build6/packet/tests_r6'")
s=s.replace("str(root/'pytest')", "str(root/('pytest_'+str(os.getpid())))")
s=s.replace('200*1024**2','200_000_000')
s=s.replace('proof.mkdir(parents=True,exist_ok=True)', "proof.mkdir(parents=True,exist_ok=True)\n(proof/'work/test_artifacts_r6').mkdir(parents=True,exist_ok=True)")
# Reuse the build-5 exact-code fingerprint; monitor Python line events without
# tracing unrelated scientific-library frames. This preserves the denominator.
runner=(B/'test_runner.py').read_text()
start=runner.index('def code_digest(code):');end=runner.index('mon = sys.monitoring')
fingerprint=runner[start:end].replace('snapshots={};expected_codes={};rejected_codes={}', 'snapshots={};expected_codes={};rejected_codes={}')
s=s.replace('import signal','import signal\nimport types\nimport hashlib')
s=s.replace('import pytest', '''import subprocess
_run=subprocess.run
def file_script_run(command, **kwargs):
    if '-c' in command:
        i=command.index('-c');code=command[i+1]
        script=proof/('subprocess_'+hashlib.sha256(code.encode()).hexdigest()[:12]+'.py')
        script.write_text(code)
        command=command[:i]+[str(script)]+command[i+2:]
    return _run(command,**kwargs)
subprocess.run=file_script_run
import pytest''')
s=s.replace('cov=Coverage()', 'cov=Coverage()\n'+fingerprint+'''
mon=sys.monitoring
mon.use_tool_id(4,'packet-proof')
def started(code, offset):
    if code.co_filename in expected_codes:
        if code_digest(code) in expected_codes[code.co_filename]:mon.set_local_events(4,code,mon.events.LINE)
        else:rejected_codes[code.co_filename]=rejected_codes.get(code.co_filename,0)+1
    return mon.DISABLE
def hit(code, number):
    rel=str(Path(code.co_filename).relative_to(tree))
    cov.hits.setdefault(rel,{}).setdefault(str(number),set()).add(cov.current)
    return mon.DISABLE
mon.register_callback(4,mon.events.PY_START,started)
mon.register_callback(4,mon.events.LINE,hit)
''')
s=s.replace("if not sys.argv[3].startswith('base') and not os.environ.get('R6_NO_TRACE'):sys.settrace(cov.trace)","mon.set_events(4,mon.events.PY_START)")
s=s.replace('sys.settrace(None)', 'mon.set_events(4,0)')
s=s.replace("(proof/'temporary_sizes.json').write_text", "coverage=proof/'coverage'\ncoverage.mkdir(exist_ok=True)\n(coverage/'source_hashes.json').write_text(json.dumps(snapshots))\n(coverage/'hits.json').write_text(json.dumps({k:sorted(int(n) for n in v) for k,v in cov.hits.items()}))\n(coverage/'results.json').write_text(json.dumps(dict(coverage_code_filter='compiled-source fingerprint')))\n(proof/'temporary_sizes.json').write_text")
(B/'packet_final.py').write_text(s)
(B/'PACKET_PATH_ADAPTATIONS.diff').write_text(''.join(edits))
(B/'PACKET_MONITOR.diff').write_text(''.join(difflib.unified_diff((B/'packet_runner.py').read_text().splitlines(True),s.splitlines(True),fromfile='relocated original runner',tofile='final runner')))
print('Assertions unchanged; fixture root points into the fixed proof folder. Missing supporting inputs remain missing.')
