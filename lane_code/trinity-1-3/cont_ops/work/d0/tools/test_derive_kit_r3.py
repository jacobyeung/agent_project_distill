"""Tests for derive_kit.py: identity reproduction, a consistent D0 stand-in, and refusals of inconsistent overrides."""
import copy, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import derive_kit as dk
W = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0'); KIT = W / 'kitfull'; T = Path(tempfile.mkdtemp(dir=W / 'testruns'))
L = dk.AS + 'ap/8865619b'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
fails = 0
def check(name, cond):
    global fails; fails += not cond; print('OK ' if cond else 'BAD', name)
def refused(name, over, needle):
    try:
        dk.derive(KIT, T / name, over); check(name + ' (should refuse)', False)
    except ValueError as e:
        check(f'{name}: {e}'[:150], needle in str(e))

# T1: identity reproduction (fixture: two large tars are not on this node)
r = dk.derive(KIT, T / 't1', {'fixture': True})
for f in ('k/0.json', 'k/1.json', 'k/b02e4385.json', 'k/7.json'):
    check('T1 byte-identical ' + f, (KIT / f).read_bytes() == (T / 't1' / f).read_bytes())
lt = json.loads((T / 't1/k/launch.json').read_text()); lb = json.loads((KIT / 'k/launch.json').read_text())
check('T1 fixture launch = sealed except status FIXTURE/unauthorized', lt['status'] == 'FIXTURE' and lt['production_authorized'] is False and {k: v for k, v in lt.items() if k not in ('status', 'production_authorized')} == {k: v for k, v in lb.items() if k not in ('status', 'production_authorized')})
base_m = [l for l in (KIT / 'SHA256SUMS.txt').read_text().splitlines() if l.split('  ', 1)[1] not in r['absent_source_files']]
check('T1 manifest equal except absent tars and launch.json', [l for l in base_m if 'k/launch.json' not in l] == [l for l in (T / 't1/SHA256SUMS.txt').read_text().splitlines() if 'k/launch.json' not in l])
check('T1 absent files are exactly the two tars', sorted(r['absent_source_files']) == ['k/np226_5204b3a0.tar', 'k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar'])
refused('T1 without fixture', {}, 'source kit files absent')

# A consistent D0 stand-in
S = W / 'standin_rows'
cfg0 = json.loads((KIT / 'k/b02e4385.json').read_text()); cur0 = json.loads((KIT / 'k/0.json').read_text())
art = json.loads((W / 'base/runs/469ddece/m544/artifact.json').read_text())
init_path = dk.AS + 'ap/d0i11111111/m544/artifact.json'; A544 = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
pool = json.loads((KIT / 'k/pool_selection.json').read_text()); pool['sources']['ROUTE_direct']['status'] = 'DEFERRED'
pool['sources']['ROUTE_direct']['reason'] = 'moved_to_vqa_store_d0'
(T / 'pool_selection.json').write_text(dk.enc(pool) + '\n')
dev = json.loads((KIT / 'k/dev_scene_exclusions.json').read_text()); dev['STANDIN'] = True
(T / 'dev_scene_exclusions.json').write_text(dk.enc(dev) + '\n')
vq, ro = S / 'vqa_receipt.json', S / 'routing_receipt.json'
tars = [t for t in cur0['tars'] if not any(k.startswith('ap/f2ad01ad/runs/49becb79/m200/') for k in t['files'])]
tars = [t for t in tars if not any(k.startswith('ap/5e1d07a4/f/h/r16/') for k in t['files'])] + [t for t in tars if any(k.startswith('ap/5e1d07a4/f/h/r16/') for k in t['files'])]
tars += [dict(parts=['/project/community/jjyeung/distill/okit/in/cr/STANDIN_d0rows.p00'],
              files={'ap/8865619b/u/d0rows/vqa/receipt.json': sha(vq), 'ap/8865619b/u/d0rows/routing/receipt.json': sha(ro)}),
         dict(parts=['/project/community/jjyeung/distill/okit/in/cr/STANDIN_m544.p00'],
              files={'ap/d0i11111111/m544/artifact.json': A544, 'ap/8865619b/runs/469ddece/m544/heads.pt': art['heads']['sha256'],
                     'ap/8865619b/runs/469ddece/m544/full_weights/full_weights.json': art['full_weights']['sha256']})]
psel = dict(path=dk.KIT_LOGICAL + 'pool_selection.json', sha256=sha(T / 'pool_selection.json'))
dexc = dict(path=dk.KIT_LOGICAL + 'dev_scene_exclusions.json', sha256=sha(T / 'dev_scene_exclusions.json'))
catalog = {**cfg0['s1_routing']['catalog'], psel['sha256']: psel['path'], dexc['sha256']: dexc['path']}
D0 = dict(fixture=True, run_key='11111111', kit_key='22222222', persistent_run_root='/project/community/jjyeung/okh7/r/33333333',
          config=dict(streams=dict(vqa=dict(path=L + '/u/d0rows/vqa/receipt.json', sha256=sha(vq)),
                                   routing=dict(path=L + '/u/d0rows/routing/receipt.json', sha256=sha(ro))),
                      init_artifact=dict(artifact=dict(path=init_path, sha256=A544), lm='full', heads=['pose', 'depth']),
                      s1_routing=dict(selection=psel, catalog=catalog), dev_scene_exclusions=dexc),
          deployment=dict(init=dict(file=init_path, sha256=A544), tars=tars),
          add_k={'pool_selection.json': dict(path=str(T / 'pool_selection.json'), sha256=psel['sha256']),
                 'dev_scene_exclusions.json': dict(path=str(T / 'dev_scene_exclusions.json'), sha256=dexc['sha256'])})
r2 = dk.derive(KIT, T / 'd0', D0)
L2 = json.loads((T / 'd0/k/launch.json').read_text()); C2 = json.loads((T / 'd0/k' / (r2['config_key'] + '.json')).read_text())
check('D0 status FIXTURE, not authorized', L2['status'] == 'FIXTURE' and L2['production_authorized'] is False)
check('D0 inherited_streams = config streams', L2['inherited_streams'] == C2['streams'])
check('D0 source_selection = new pool pin', L2['source_selection'] == psel)
check('D0 run paths', C2['output'].endswith('/11111111') and C2['preparation_output'].endswith('/11111111')
      and L2['run_directory'].endswith('/11111111') and L2['in_job_admission']['directory'] == C2['output'] + '/inputs')
check('D0 ANON_OK placeholder bound to manifest', json.loads((T / 'd0/ANON_OK.json').read_text())['manifest_sha256'] == sha(T / 'd0/SHA256SUMS.txt'))
diff = sorted(k for k in set(cfg0) | set(C2) if cfg0.get(k) != C2.get(k))
check('D0 config changes only data fields: ' + ','.join(diff), set(diff) <= {'streams', 'init_artifact', 's1_routing', 'dev_scene_exclusions', 'output', 'preparation_output'})
check('D0 b/ and job scripts unchanged', all((KIT / p).read_bytes() == (T / 'd0' / p).read_bytes() for p in ['job.sh', 'job8.sh'] + [str(x.relative_to(KIT)) for x in (KIT / 'b').rglob('*') if x.is_file()]))
# Refusals
def mut(f):
    o = copy.deepcopy(D0); f(o); return o
refused('streams only (0.json not staging them)', mut(lambda o: (o.pop('deployment'), o['config'].pop('init_artifact'))), 'not staged')
refused('init only in config', mut(lambda o: o['deployment'].pop('init')), 'init_artifact and k/0.json init differ')
refused('init only in deployment', mut(lambda o: o['config'].pop('init_artifact')), 'without config init_artifact')
refused('old m200 still staged', mut(lambda o: o['deployment'].__setitem__('tars', cur0['tars'] + tars[-2:])), 'old init')
refused('pool file without config pin', mut(lambda o: o['config'].pop('s1_routing')), 'does not pin it')
refused('pool pin without file', mut(lambda o: o['add_k'].pop('pool_selection.json')), 'without the new k/pool_selection.json')
refused('recipe change', mut(lambda o: o['config'].__setitem__('recipe', {})), 'outside the data-only set')
refused('pose stream change', mut(lambda o: o['config']['streams'].__setitem__('pose', {})), 'only the vqa and routing')
refused('add_k traversal', mut(lambda o: o['add_k'].__setitem__('../b/g.py', dict(path=str(vq), sha256=sha(vq)))), 'not allowed')
refused('run_key only', mut(lambda o: (o.pop('kit_key'), o.pop('persistent_run_root'))), 'new run_key, kit_key and persistent_run_root')
refused('root under /home', mut(lambda o: o.__setitem__('persistent_run_root', '/home/jjyeung/okit/r/33333333')), 'not be under /home')
refused('READY on fixture', mut(lambda o: o.__setitem__('status', 'READY')), 'never be READY')
refused('identity only (run_key)', {'fixture': True, 'run_key': '11111111'}, 'new run_key, kit_key and persistent_run_root')
refused('root equal modulo slash', mut(lambda o: o.__setitem__('persistent_run_root', '/home/jjyeung/okit/r/5da50f2b/')), 'new run_key, kit_key and persistent_run_root')
refused('init heads change', mut(lambda o: o['config']['init_artifact'].__setitem__('heads', ['pose'])), 'only its artifact pin')
refused('conflicting extra and tars', mut(lambda o: o['deployment'].__setitem__('extra', cur0['extra'] + [dict(dest=L + '/u/d0rows/vqa/receipt.json', sha256='0'*64, parts=[])])), 'two different files')
ok = mut(lambda o: o['config']['streams'].__setitem__('routing', cfg0['streams']['routing']))
try:
    dk.derive(KIT, T / 'vqa_only_explicit_routing', ok); check('VQA change with unchanged routing repeated is accepted', True)
except ValueError as e: check('VQA change with unchanged routing repeated is accepted: ' + str(e), False)
refused('unknown top key', mut(lambda o: o.__setitem__('drop_k', ['4.json'])), 'unknown override keys')
# Gate binding: the kit's own g.py on the derived D0 kit (status flipped to READY in the test copy only)
ident = r2['config_identity']; contract = None
sys.path.insert(0, str(T / 'd0/b'))
import d as kitd
contract = kitd.digest(kitd.contract(L2, C2))
review = dict(verdict='PASS', reviewer='TEST', config_sha256=ident, admission_contract_sha256=contract, admission_scope='pinned-template-and-native-data-derivation')
staging = dict(status='PASS', source_revision=L2['source_revision'], config_sha256=ident, missing=[], project_community_write_bytes=0)
auth = json.loads((KIT / 'k/4.json').read_text()); auth['config_sha256'] = ident
for n, v in (('review', review), ('staging', staging), ('4', auth)): (T / f'{n}.json').write_text(dk.enc(v) + '\n')
D0g = mut(lambda o: o['add_k'].update({f'{n}.json': dict(path=str(T / f'{n}.json'), sha256=sha(T / f'{n}.json')) for n in ('review', 'staging', '4')}))
r3 = dk.derive(KIT, T / 'd0g', D0g)
check('identity unchanged by review records', r3['config_identity'] == ident)
lj = T / 'd0g/k/launch.json'; v = json.loads(lj.read_text()); v.update(status='READY', production_authorized=True); lj.write_text(dk.enc(v) + '\n')
(T / 'persist').mkdir()
def gate(kitdir):
    v = json.loads((kitdir / 'k/launch.json').read_text()); v['persistent_run_root'] = str(T / 'persist' / kitdir.name); (kitdir / 'k/launch.json').write_text(dk.enc(v) + '\n')
    p = subprocess.run(['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--proc', '/proc', '--tmpfs', '/tmp', '--bind', str(T), str(T),
                        '--setenv', 'SLURM_JOB_ID', '999001', '/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-B', '-c',
                        'import sys; sys.path.insert(0, sys.argv[1]+"/b"); import g; g.check(sys.argv[1], None, "p"); print("GATE_PASS")', str(kitdir)],
                       capture_output=True, text=True)
    return (p.stdout + p.stderr).strip().splitlines()[-1]
out = gate(T / 'd0g'); check('g.py check p PASS on derived D0 kit: ' + out, out == 'GATE_PASS')
r4 = dk.derive(KIT, T / 'd0old', D0)  # old review/staging carried
lj = T / 'd0old/k/launch.json'; v = json.loads(lj.read_text()); v.update(status='READY', production_authorized=True); lj.write_text(dk.enc(v) + '\n')
out = gate(T / 'd0old'); check('g.py refuses the old review: ' + out[:90], 'not bound to the launch configuration' in out)
print('FAILS', fails); sys.exit(1 if fails else 0)
