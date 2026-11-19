from pathlib import Path
import difflib
import hashlib
import subprocess
import tempfile

L=Path('/scratch/jjyeung/orch_n30/so_syncfix')
root=L/'work/round1'
source=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/syncin')
names=['lane_code_filter.py','lane_code_sync.sh','tssh.sh','lane_code_scan.py','sync_health.py']
(root/'PREIMAGE.sha256').write_text(''.join(hashlib.sha256((source/name).read_bytes()).hexdigest()+'  tools/'+name+'\n' for name in names))
(root/'POSTIMAGE.sha256').write_text(''.join(hashlib.sha256((root/'tools'/name).read_bytes()).hexdigest()+'  tools/'+name+'\n' for name in names+['lane_code_stage.sh','lane_code_log.py']))
groups={
    '01_filter.diff': ['tools/lane_code_filter.py','tests/test_filter.py','inputs/lane_code_filter.py','inputs/lane_code_filter.py.orig'],
    '02_stage_driver.diff': ['tools/lane_code_sync.sh','tools/lane_code_stage.sh','tools/lane_code_log.py','tests/test_log.py','tests/support.py','tests/test_driver.py','tests/test_review.py','tests/run_tests.py','tests/check_delivery.py','inputs/lane_code_sync.sh'],
    '03_tssh.diff': ['tools/tssh.sh','tests/test_wrapper.py','inputs/tssh.sh'],
    '04_atomic_scan.diff': ['tools/lane_code_scan.py','tests/test_slots.py','tests/test_install.py','inputs/lane_code_scan.py','inputs/sync_health.py','install_tools.py','calibrate_budgets.py','PREIMAGE.sha256','POSTIMAGE.sha256'],
}
(root/'patches').mkdir(exist_ok=True)

def delta(name):
    existing=source/Path(name).name
    old=existing.read_text() if name.startswith('tools/') and existing.exists() else ''
    new=(root/name).read_text()
    return ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
                    fromfile='a/'+name if old else '/dev/null',tofile='b/'+name))

for name, paths in groups.items():
    (root/'patches'/name).write_text(''.join(delta(path) for path in paths))
(root/'INSTALL_TOOLS.diff').write_text(''.join(delta('tools/'+name) for name in names+['lane_code_stage.sh','lane_code_log.py']))
replay=Path(tempfile.mkdtemp(prefix='round1_patchcheck_',dir=str(L/'work')))
(replay/'tools').mkdir()
for name in names:
    (replay/'tools'/name).write_bytes((source/name).read_bytes())
log=[]
def command(args):
    log.append('$ '+' '.join(str(x) for x in args))
    result=subprocess.run([str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log.append(result.stdout.decode())
    if result.returncode: raise RuntimeError(log[-1])
for name in groups:
    command(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-d',replay,'-i',root/'patches'/name])
for paths in groups.values():
    for name in paths:
        assert (root/name).read_bytes()==(replay/name).read_bytes(),name
log.append('PASS: numbered patches reproduce every tool, test, input, installer, and hash file byte-for-byte.\n')
install=Path(tempfile.mkdtemp(prefix='round1_installcheck_',dir=str(L/'work')))
(install/'tools').mkdir()
for name in names:
    (install/'tools'/name).write_bytes((source/name).read_bytes())
command(['patch','--dry-run','--batch','--fuzz=0','-p1','-d',install,'-i',root/'INSTALL_TOOLS.diff'])
command(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-d',install,'-i',root/'INSTALL_TOOLS.diff'])
for name in names+['lane_code_stage.sh','lane_code_log.py']:
    assert (root/'tools'/name).read_bytes()==(install/'tools'/name).read_bytes(),name
log.append('PASS: INSTALL_TOOLS.diff reproduces all seven postimage tools.\n')
for name in ['lane_code_sync.sh','lane_code_stage.sh','tssh.sh']:
    command(['bash','-n',install/'tools'/name])
for path in (replay/'tools').glob('*.py'):
    compile(path.read_bytes(),str(path),'exec')
log.append('PASS: shell syntax and Python compilation.\n')
(root/'logs/package_check.txt').write_text('\n'.join(log))
(L/'work/round1_patchcheck_path.txt').write_text(str(replay)+'\n')
print('REPLAY '+str(replay))
print('INSTALL '+str(install))
print('PASS: four numbered patches, tools-only patch, content comparisons, and syntax checks.')
