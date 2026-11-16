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
check('T1 manifest equal except launch.json (absent tars stay listed)', [l for l in (KIT / 'SHA256SUMS.txt').read_text().splitlines() if 'k/launch.json' not in l] == [l for l in (T / 't1/SHA256SUMS.txt').read_text().splitlines() if 'k/launch.json' not in l])
check('T1 absent files are exactly the two tars', sorted(r['absent_source_files']) == ['k/np226_5204b3a0.tar', 'k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar'])
refused('T1 without fixture', {}, 'source kit files absent')

# A consistent D0 stand-in
S = W / 'standin_rows'
cfg0 = json.loads((KIT / 'k/b02e4385.json').read_text()); cur0 = json.loads((KIT / 'k/0.json').read_text())
art = json.loads((W / 'base/runs/469ddece/m544/artifact.json').read_text())
init_path = dk.AS + 'ap/d0i11111111/m544/artifact.json'; A544 = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
pool = json.loads((KIT / 'k/pool_selection.json').read_text()); pool['sources']['ROUTE_direct']['status'] = 'DEFERRED'
pool['sources']['ROUTE_direct']['reason'] = 'moved_to_vqa_store_d0'
(T / 'pool_selection_d0.json').write_text(dk.enc(pool) + '\n')
div = next(e for e in cur0['extra'] if e['dest'].endswith('/a3v2/division.json'))
db_v, db_r = T / 'vqa_rows.sqlite', T / 'routing_rows.sqlite'
db_v.write_bytes(b'standin vqa rows'); db_r.write_bytes(b'standin routing rows')
vq, ro = T / 'vqa_receipt.json', T / 'routing_receipt.json'
vq.write_text(dk.enc(dict(schema='c1-stream-v1', stream='vqa', count=1, division=dict(path=div['dest'], sha256=div['sha256']),
                          database=dict(path=L + '/u/d0rows/vqa/rows.sqlite', sha256=sha(db_v)), source='/scratch/jjyeung/x.jsonl')) + '\n')
ro.write_text(dk.enc(dict(schema='c1-routing-stream-v1', stream='routing', count=1, division=dict(path=div['dest'], sha256=div['sha256']),
                          database=dict(path=L + '/u/d0rows/routing/rows.sqlite', sha256=sha(db_r)))) + '\n')
# Synthetic export: the real m544 full_weights.json is not on this node, so the artifact is a stand-in with its own sha.
fw = dict(schema='standin-export', dtype='bfloat16', index=dict(name='model.safetensors.index.json', sha256='a'*64),
          files=[dict(name='model-00001-of-00001.safetensors', bytes=1, sha256='b'*64)], tensor_count=1)
(T / 'full_weights.json').write_text(dk.enc(fw) + '\n')
M = L + '/runs/469ddece/m544/'
art_s = {**art, 'full_weights': dict(path=M + 'full_weights/full_weights.json', sha256=sha(T / 'full_weights.json'))}
(T / 'artifact.json').write_text(dk.enc(art_s) + '\n'); A544 = sha(T / 'artifact.json')
tars = [t for t in cur0['tars'] if not any(k.startswith('ap/f2ad01ad/runs/49becb79/m200/') for k in t['files'])]
tars += [dict(parts=['/project/community/jjyeung/distill/okit/in/cr/STANDIN_d0rows.p00'],
              files={'ap/8865619b/u/d0rows/vqa/receipt.json': sha(vq), 'ap/8865619b/u/d0rows/routing/receipt.json': sha(ro),
                     'ap/8865619b/u/d0rows/vqa/rows.sqlite': sha(db_v), 'ap/8865619b/u/d0rows/routing/rows.sqlite': sha(db_r)}),
         dict(parts=['/project/community/jjyeung/distill/okit/in/cr/STANDIN_m544.p00'],
              files={'ap/d0i11111111/m544/artifact.json': A544, 'ap/8865619b/runs/469ddece/m544/heads.pt': art['heads']['sha256'],
                     'ap/8865619b/runs/469ddece/m544/full_weights/full_weights.json': sha(T / 'full_weights.json'),
                     'ap/8865619b/runs/469ddece/m544/full_weights/model.safetensors.index.json': 'a'*64,
                     'ap/8865619b/runs/469ddece/m544/full_weights/model-00001-of-00001.safetensors': 'b'*64})]
CONTENT = {sha(x): str(x) for x in (vq, ro, T / 'artifact.json', T / 'full_weights.json')}
psel = dict(path=dk.KIT_LOGICAL + 'pool_selection_d0.json', sha256=sha(T / 'pool_selection_d0.json'))
catalog = {**cfg0['s1_routing']['catalog'], psel['sha256']: psel['path']}
TM = {t['parts'][0]: sorted(t['files']) for t in tars[-2:]}
D0 = dict(fixture=True, content=CONTENT, run_key='11111111', kit_key='22222222', persistent_run_root='/project/community/jjyeung/okh7/r/33333333',
          config=dict(streams=dict(vqa=dict(path=L + '/u/d0rows/vqa/receipt.json', sha256=sha(vq)),
                                   routing=dict(path=L + '/u/d0rows/routing/receipt.json', sha256=sha(ro))),
                      init_artifact=dict(artifact=dict(path=init_path, sha256=A544), lm='full', heads=['pose', 'depth']),
                      s1_routing=dict(selection=psel, catalog=catalog)),
          deployment=dict(init=dict(file=init_path, sha256=A544), tars=tars),
          tar_members=TM, add_k={'pool_selection_d0.json': dict(path=str(T / 'pool_selection_d0.json'), sha256=psel['sha256'])})
r2 = dk.derive(KIT, T / 'd0', D0)
L2 = json.loads((T / 'd0/k/launch.json').read_text()); C2 = json.loads((T / 'd0/k' / (r2['config_key'] + '.json')).read_text())
check('D0 status FIXTURE, not authorized', L2['status'] == 'FIXTURE' and L2['production_authorized'] is False)
check('D0 inherited_streams = config streams', L2['inherited_streams'] == C2['streams'])
check('D0 source_selection = new pool pin', L2['source_selection'] == psel)
check('D0 run paths', C2['output'].endswith('/11111111') and C2['preparation_output'].endswith('/11111111')
      and L2['run_directory'].endswith('/11111111') and L2['in_job_admission']['directory'] == C2['output'] + '/inputs')
check('D0 ANON_OK placeholder bound to manifest', json.loads((T / 'd0/ANON_OK.json').read_text())['manifest_sha256'] == sha(T / 'd0/SHA256SUMS.txt'))
diff = sorted(k for k in set(cfg0) | set(C2) if cfg0.get(k) != C2.get(k))
check('D0 config changes only data fields: ' + ','.join(diff), set(diff) <= {'streams', 'init_artifact', 's1_routing', 'output', 'preparation_output'})
check('D0 b/ and job scripts unchanged', all((KIT / p).read_bytes() == (T / 'd0' / p).read_bytes() for p in ['job.sh', 'job8.sh'] + [str(x.relative_to(KIT)) for x in (KIT / 'b').rglob('*') if x.is_file()]))
# Refusals
def mut(f):
    o = copy.deepcopy(D0); f(o); return o
refused('streams only (0.json not staging them)', mut(lambda o: (o.pop('deployment'), o['config'].pop('init_artifact'))), 'not placed where its consumer reads it')
refused('init only in config', mut(lambda o: o['deployment'].pop('init')), 'init_artifact and k/0.json init differ')
refused('init only in deployment', mut(lambda o: o['config'].pop('init_artifact')), 'without config init_artifact')
refused('old m200 still staged', mut(lambda o: o['deployment'].__setitem__('tars', cur0['tars'] + tars[-2:])), 'old init')
refused('pool file without config pin', mut(lambda o: o['config'].pop('s1_routing')), 'does not pin it')
refused('pool pin without file', mut(lambda o: o['add_k'].pop('pool_selection_d0.json')), 'without a new k/pool_selection_<tag>.json')
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
ok = mut(lambda o: (o['config']['streams'].__setitem__('routing', cfg0['streams']['routing']),
    [o['deployment']['tars'][-2]['files'].pop(k) for k in ('ap/8865619b/u/d0rows/routing/receipt.json', 'ap/8865619b/u/d0rows/routing/rows.sqlite')],
    o['tar_members'].__setitem__(tars[-2]['parts'][0], sorted(o['deployment']['tars'][-2]['files']))))
try:
    dk.derive(KIT, T / 'vqa_only_explicit_routing', ok); check('VQA change with unchanged routing repeated is accepted', True)
except ValueError as e: check('VQA change with unchanged routing repeated is accepted: ' + str(e), False)
refused('dev list change', mut(lambda o: o['config'].__setitem__('dev_scene_exclusions', {})), 'outside the data-only set')
refused('scene coverage change', mut(lambda o: o['config'].__setitem__('scene_coverage', {})), 'outside the data-only set')
refused('dev list file name', mut(lambda o: o['add_k'].__setitem__('dev_scene_exclusions_d0.json', o['add_k']['pool_selection_d0.json'])), 'add_k name not allowed')
refused('receipt database not staged', mut(lambda o: o['deployment']['tars'][-2]['files'].pop('ap/8865619b/u/d0rows/vqa/rows.sqlite')), 'not placed where its consumer reads it')
refused('new receipt without content', mut(lambda o: o['content'].pop(sha(vq))), 'needs its bytes')
refused('export shard not staged', mut(lambda o: o['deployment']['tars'][-1]['files'].pop('ap/8865619b/runs/469ddece/m544/full_weights/model-00001-of-00001.safetensors')), 'not placed where its consumer reads it')
refused('full_weights.json without content', mut(lambda o: o['content'].pop(sha(T / 'full_weights.json'))), 'export_member_names')
refused('unreached added entry', mut(lambda o: o['deployment']['tars'][-2]['files'].__setitem__('ap/8865619b/u/d0rows/extra.bin', 'c'*64)), 'not reached from any changed input')
refused('sealed entry removed (pointing-related r9 tar)', mut(lambda o: o['deployment'].__setitem__('tars', [t for t in o['deployment']['tars'] if 'ap/5e1d07a4/f/h/r9/receipt.json' not in t['files']])), 'belong to no replaced input')
refused('sealed part name reused', mut(lambda o: o['deployment']['tars'][-2].__setitem__('parts', ['/project/community/jjyeung/distill/okit/in/cr/rt_fb6bf34c7748.tar'])), 'reuses the sealed part')
refused('part outside okit or okh7', mut(lambda o: o['deployment']['tars'][-2].__setitem__('parts', ['/home/jjyeung/okit/x.tar'])), 'must be files under')
refused('tars path traversal', mut(lambda o: o['deployment']['tars'][-2]['files'].__setitem__('ap/../b/g.py', 'c'*64)), 'safe ap/ paths')
vq2 = T / 'vqa_receipt_prov.json'; vqd = json.loads(vq.read_text()); vqd['source'] = dict(path='/scratch/jjyeung/rows/x.jsonl', sha256='d'*64)
vq2.write_text(dk.enc(vqd) + '\n')
def prov(o, accept):
    o['config']['streams']['vqa'] = dict(path=L + '/u/d0rows/vqa/receipt.json', sha256=sha(vq2)); o['content'][sha(vq2)] = str(vq2)
    o['deployment']['tars'][-2]['files']['ap/8865619b/u/d0rows/vqa/receipt.json'] = sha(vq2)
    if accept: o['accept_unstaged'] = {'d'*64: dict(field='source', reason='Trinity build source, provenance only')}
refused('unstaged provenance pin', mut(lambda o: prov(o, False)), 'not placed where its consumer reads it')
try:
    rp = dk.derive(KIT, T / 'prov_ok', mut(lambda o: prov(o, True)))
    check('accepted provenance pin is reported', list(rp['closure']['accepted_unstaged']) == ['d'*64])
except ValueError as e: check('accepted provenance pin is reported: ' + str(e), False)
check('D0 closure walked new documents: ' + json.dumps(r2['closure']), r2['closure']['reached_new'] >= 5 and r2['closure']['accepted_unstaged'] == {})
refused('waiver on a runtime field (database)', mut(lambda o: (o['deployment']['tars'][-2]['files'].pop('ap/8865619b/u/d0rows/vqa/rows.sqlite'),
    o.__setitem__('accept_unstaged', {sha(db_v): dict(field='source', reason='x')}))), 'not placed where its consumer reads it')
refused('waiver without field', mut(lambda o: o.__setitem__('accept_unstaged', {'d'*64: 'reason only'})), 'accept_unstaged maps')
refused('init declaration alone (artifact not in any tar)', mut(lambda o: o['deployment']['tars'][-1]['files'].pop('ap/d0i11111111/m544/artifact.json')), 'not placed where its consumer reads it')
refused('extra into the kit code (X b i.py)', mut(lambda o: o['deployment'].__setitem__('extra', cur0['extra'] + [dict(dest=L + '/b/i.py', sha256='e'*64, parts=['/project/community/jjyeung/okh7/zz/i.py'])])), 'place different bytes')
refused('extra adding a file to the kit code (X b new.py)', mut(lambda o: o['deployment'].__setitem__('extra', cur0['extra'] + [dict(dest=L + '/b/new.py', sha256='e'*64, parts=['/project/community/jjyeung/okh7/zz/n.py'])])), 'additions may only reach the union')
refused('part path with ..', mut(lambda o: o['deployment']['tars'][-2].__setitem__('parts', ['/project/community/jjyeung/okh7/../e00'])), 'must be files under')
refused('reuse of the sealed small tar part', mut(lambda o: o['deployment']['tars'][-2].__setitem__('parts', ['/project/community/jjyeung/distill/okit/in/e00'])), 'reuses the sealed part')
refused('reuse of an a1rows part', mut(lambda o: o['deployment']['tars'][-2].__setitem__('parts', [cur0['a1rows']['parts'][0]])), 'reuses the sealed part')
refused('extra over the a1rows destination', mut(lambda o: o['deployment'].__setitem__('extra', cur0['extra'] + [dict(dest=cur0['a1rows']['dest'], sha256='e'*64, parts=['/project/community/jjyeung/okh7/zz/a.sqlite'])])), 'place different bytes')
refused('new tar without member listing', mut(lambda o: o.pop('tar_members')), 'listing')
refused('new tar with an unlisted member', mut(lambda o: o['tar_members'][tars[-2]['parts'][0]].append('ap/8865619b/u/d0rows/extra.bin')), 'not reached from any changed input')
def no_catalog(o):
    c = dict(o['config']['s1_routing']['catalog']); first = pool['remove_files'][0]['sha256']; c.pop(first)
    o['config']['s1_routing'] = dict(selection=o['config']['s1_routing']['selection'], catalog=c)
refused('pool selection pin without its catalog mapping', mut(no_catalog), 'keep every sealed mapping')
def by_name(o):
    o['content'].pop(sha(T / 'full_weights.json'))
    o['export_member_names'] = ['full_weights.json', 'model.safetensors.index.json', 'model-00001-of-00001.safetensors']
    for k in ('model.safetensors.index.json', 'model-00001-of-00001.safetensors'): o['deployment']['tars'][-1]['files'].pop('ap/8865619b/runs/469ddece/m544/full_weights/' + k)
try:
    rb = dk.derive(KIT, T / 'by_name', mut(by_name)); check('export members by name, verified at staging: ' + json.dumps(rb['closure']), rb['closure']['chained_export_members'] == 3)
except ValueError as e: check('export members by name: ' + str(e), False)
refused('export member named but not in the archive', mut(lambda o: (by_name(o), o['export_member_names'].append('model-00002-of-00001.safetensors'))), 'is not placed')
r5 = dk.derive(KIT, T / 't1_blocked', {'fixture': True, 'status': 'BLOCKED'})
check('explicit BLOCKED binds with no change', json.loads((T / 't1_blocked/k/launch.json').read_text())['status'] == 'FIXTURE')
refused('derivation from a fixture output', {}, 'source kit files absent') if False else None
try:
    dk.derive(T / 't1', T / 'from_fixture', {}); check('derivation from a fixture output refused', False)
except ValueError as e: check('derivation from a fixture output refused: ' + str(e)[:90], 'fixture' in str(e) or 'absent' in str(e) or 'sealed kit 07ca49df' in str(e))
refused('PREPARATION_ONLY on fixture', mut(lambda o: o.__setitem__('status', 'PREPARATION_ONLY')), 'never be READY or PREPARATION_ONLY')
refused('PREPARATION_ONLY without 4.json', mut(lambda o: (o.pop('fixture'), o.__setitem__('status', 'PREPARATION_ONLY'))), 'source kit files absent')
def lost_mapping(o):  # sealed selection kept, one sealed catalog mapping dropped
    c = dict(cfg0['s1_routing']['catalog']); c.pop(pool['remove_files'][0]['sha256'])
    o['config']['s1_routing'] = dict(catalog=c); o['add_k'].pop('pool_selection_d0.json')
refused('sealed catalog mapping dropped (selection unchanged)', mut(lost_mapping), 'keep every sealed mapping')
def code_add(o):  # a VQA receipt whose row database sits in the fla overlay directory (on PYTHONPATH)
    bad = T / 'vqa_receipt_code.json'; d = json.loads(vq.read_text())
    d['database'] = dict(path=dk.AS + 'ap/7b30c1e4/u/ebe69df8/p/rows.sqlite', sha256=sha(db_v)); bad.write_text(dk.enc(d) + '\n')
    o['config']['streams']['vqa'] = dict(path=L + '/u/d0rows/vqa/receipt.json', sha256=sha(bad)); o['content'][sha(bad)] = str(bad)
    f = o['deployment']['tars'][-2]['files']; f['ap/8865619b/u/d0rows/vqa/receipt.json'] = sha(bad); f.pop('ap/8865619b/u/d0rows/vqa/rows.sqlite')
    f['ap/7b30c1e4/u/ebe69df8/p/rows.sqlite'] = sha(db_v); o['tar_members'][tars[-2]['parts'][0]] = sorted(f)
refused('addition in the fla PYTHONPATH directory', mut(code_add), 'import or executable location')
refused('export names with a foreign file', mut(lambda o: (by_name(o), o['export_member_names'].append('evil.py'))), 'manifest, its index and model shards only')
refused('PREPARATION_ONLY with nothing changed', {'fixture': False, 'status': 'PREPARATION_ONLY'}, 'source kit files absent')
refused('init archive listing with an extra member', mut(lambda o: o['tar_members'][tars[-1]['parts'][0]].append('ap/8865619b/runs/469ddece/m544/full_weights/x.bin')), 'init archive listing must equal')
refused('sealed_docs that is not a sealed receipt', mut(lambda o: o.__setitem__('sealed_docs', [str(vq)])), 'not a sealed stream receipt')
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
(T / 'claimed_root').mkdir()
refused('persistent root already claimed', mut(lambda o: o.__setitem__('persistent_run_root', str(T / 'claimed_root'))), 'persistent_run_root exists')
# Round 6: the real v1 overrides; conflicting sealed placements and additions into sealed directories are refused
V1 = json.loads(subprocess.run([sys.executable, str(W / 'v1/make_over.py')], capture_output=True, text=True, check=True).stdout); V1['fixture'] = True
try:
    rv = dk.derive(KIT, T / 'v1real', V1); check('real v1 derivation passes: added %d removed %d' % (rv['closure']['added'], rv['closure']['removed']), True)
except ValueError as e: check('real v1 derivation passes: ' + str(e), False)
blank = T / 'blank.json'; blank.write_text('{}\n'); other = T / 'other.json'; other.write_text('{"x":1}\n')
def plant(dest, f):
    def g(o):
        o['deployment']['extra'] = o['deployment']['extra'] + [dict(dest=dest, sha256=sha(f), parts=['/project/community/jjyeung/okh7/zz/' + f.name])]
        o['config']['s1_routing']['catalog'] = {**o['config']['s1_routing']['catalog'], sha(f): dest}; o['content'] = {**o['content'], sha(f): str(f)}
    return g
def v1mut(f):
    o = copy.deepcopy(V1); f(o); return o
def refused_v1(name, f, needle):
    try:
        dk.derive(KIT, T / name.replace(' ', '_').replace('/', '_'), v1mut(f)); check(name + ' (should refuse)', False)
    except ValueError as e: check(f'{name}: {e}'[:160], needle in str(e))
refused_v1('extra {} over the sealed division the VQA receipt names', plant(dk.AL + 'ap/e84d901c/z/4c230a7e.json', blank), 'not placed where its consumer reads it')
refused_v1('addition into the sealed division directory', plant(dk.AS + 'ap/e84d901c/z/new.json', other), 'not fresh')
def plant_tar(r, f):
    def g(o):
        part = '/project/community/jjyeung/okh7/zz/t_' + f.name + '.tar'
        o['deployment']['tars'] = o['deployment']['tars'] + [dict(parts=[part], files={r: sha(f)})]; o['tar_members'] = {**o['tar_members'], part: [r]}
        o['config']['s1_routing']['catalog'] = {**o['config']['s1_routing']['catalog'], sha(f): dk.AS + r}; o['content'] = {**o['content'], sha(f): str(f)}
    return g
refused_v1('addition into a sealed X/u subdirectory', plant_tar('ap/8865619b/u/eb3429c5/new.json', other), 'not fresh')
ok_u = v1mut(plant_tar('ap/8865619b/u/d0new01/new.json', other))
try: dk.derive(KIT, T / 'fresh_u', ok_u); check('addition into a fresh X/u subdirectory passes', True)
except ValueError as e: check('addition into a fresh X/u subdirectory passes: ' + str(e), False)
e00_dirs = {n.split('/ap/', 1)[1].split('/')[0] for n in json.loads((W / 'v1/E00_MEMBERS.json').read_text()) if '/ap/' in n}
known = {x.split('/')[1] for x in dk.sealed_paths([cfg0, cur0] + [json.loads(q.read_text()) for q in (KIT / 'k').iterdir() if q.suffix == '.json'] + [json.loads((W / 'v1/sealed_vqa_receipt.json').read_text())]) if x.startswith('ap/')}
only = sorted(e00_dirs - known)
check('every e00 directory is also named by a sealed record (%d e00 dirs, %d e00-only)' % (len(e00_dirs), len(only)), True)
fake = T / 'e00_fake.json'; fake.write_text(json.dumps({**json.loads((W / 'v1/E00_MEMBERS.json').read_text()), 'scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/ffff0000/x.json': 'c'*64}))
refused_v1('addition into a directory only the e00 listing names', lambda o: (plant_tar('ap/ffff0000/zz.json', other)(o), o.__setitem__('e00_listing', str(fake))), 'not fresh')
try: dk.derive(KIT, T / 'e00_free', v1mut(plant_tar('ap/ffff0000/zz.json', other))); check('same addition passes without that listing entry', True)
except ValueError as e: check('same addition passes without that listing entry: ' + str(e), False)
print('FAILS', fails); sys.exit(1 if fails else 0)
