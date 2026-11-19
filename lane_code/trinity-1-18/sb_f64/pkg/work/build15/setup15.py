from pathlib import Path
import hashlib,json,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build15';B.mkdir(exist_ok=True)
(L/'work/tmp').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert size<1_500_000_000
(B/'BASE14_SEAL.json').write_bytes((L/'out/TREE_SEAL.json').read_bytes())
assert json.loads((B/'BASE14_SEAL.json').read_text())['tree_sha256']=='094933b3ccfd2a1057168cf8d9396a5b98ca21ae2851e673ffa15a5c7a8e4492'
(B/'START_STORAGE.json').write_text(json.dumps(dict(workspace_bytes=size,tmp_bytes=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()),scratch_free=shutil.disk_usage('/scratch').free)))
(B/'STATUS.md').write_text('# Build 15 status\n\nImplementing the init-boundary policy and export vocabulary witness. No jobs submitted.\n')
for name in ('test','opener','kits','text','row_delta','preservation','edges','confusables','mapping','packet','packet_inputs'):
    s=(L/f'work/build14/{name}14.py').read_text().replace('work/build14','work/build15').replace('B14_PROOF','B15_PROOF')
    s=s.replace('/scratch/jjyeung/orch_n30/r1_ops/work','/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/r1_ops/work')
    if name=='packet_inputs':s=s.replace('work/build13','work/build14')
    (B/f'{name}15.py').write_text(s)
(B/'run.sh').write_bytes((L/'work/build14/run.sh').read_bytes())
(B/'inputs').mkdir(exist_ok=True)
for name in ('kit_config.json','config.json'):
    (B/'inputs'/name).write_bytes((L/'work/build14/inputs'/name).read_bytes())
print('Workspace bytes:',size)
