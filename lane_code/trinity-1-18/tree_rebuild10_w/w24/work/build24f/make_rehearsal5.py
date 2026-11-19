"""Rebind immutable CPU fixture inputs to a supplied kit, without editing it."""
from pathlib import Path, PurePosixPath
from copy import deepcopy
import argparse, hashlib, json, os, subprocess, sys, tarfile
D = Path(__file__).resolve().parent; L = D.parents[1]; R = D/'rehearsal5'
OLD = D/'rehearsal4'; NS = Path('/tmp/q_22c714e1')
sys.path.insert(0, str(D))
from rehearsal_copier5 import read, put, sha, module_path
sys.path.insert(0, str(L/'work/build24'))
import joblib as J

def outside(kit):
    if (R/'PREPARATION_STARTED.json').exists():
        raise ValueError('Preparation already attempted; preserve rehearsal5; no automatic rerun')
    R.mkdir(exist_ok=True); (R/'tmp').mkdir(exist_ok=True)
    kit_seal = J.seal(kit); module, launch = module_path(kit)
    control = read(kit/'k/a.json'); assert control['GO'] is True
    archive = kit/control['source']['path']
    assert archive.resolve().is_relative_to(kit) and sha(archive) == control['source']['sha256']
    put(R/'PREPARATION_STARTED.json', dict(kit=str(kit), kit_seal=kit_seal,
        source=control['source'], copier=str(module), copier_sha256=sha(module), launch=launch,
        build24k_present_at_preparation=(L/'out/BUILD24K_REPORT.md').exists()))
    source = R/'p2/s'; source.mkdir(parents=True)
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        assert sum(m.size for m in members) < 50_000_000
        for m in members:
            name = PurePosixPath(m.name)
            assert m.isfile() and not name.is_absolute() and '..' not in name.parts
        stream.extractall(source, members=members, filter='data')
    # Preserve all old assets and replace only the final writable mount.
    args = ['--ro-bind' if x == '--bind' else x for x in J.load(OLD/'VIEW.json')]
    args += ['--bind', str(R), str(R), '--bind', str(R), str(NS),
             '--ro-bind', str(source), str(L/'work/tree_r1'),
             '--ro-bind', str(source), str(NS/'p2/s'), '--ro-bind', str(kit), str(kit)]
    for relative in ('i', 'q/p', 'q/b', 'q/twins', 'q/v.json'):
        args += ['--ro-bind', str(D/'rehearsal3/p2'/relative), str(NS/'p2'/relative)]
    args += ['--ro-bind', str(L/'work/build24d/go/p'), str(NS/'p')]
    put(R/'VIEW.json', args)
    env = {**os.environ, 'TMPDIR':str(R/'tmp'), 'S1_CPU_REHEARSAL':'1',
           'S1_REHEARSAL_ATTEMPT':'b24f_fresh', 'REHEARSAL5_KIT':str(kit)}
    with (R/'prepare.log').open('w') as log:
        result = subprocess.run(args+[sys.executable, '-I', '-s', '-B', str(Path(__file__).resolve()), str(kit), '--inside'],
                                env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode: raise RuntimeError('Preparation refused; see rehearsal5/prepare.log; no automatic retry')
    assert J.seal(kit) == kit_seal
    print('PASS: fresh kit seals, source, v.json, host/review/admission pins; old assets read-only', flush=True)

def inside(kit):
    sys.path[:0] = [str(L/'work/tree_r1'), str(L/'work/build21'), str(kit/'b')]
    import torch
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    from student_pilot import carrier_c1_run as C, r1_components as Components, r1_persisted as P
    from student_pilot import r1_rooms as Rooms, r1_direction_twins as Twins
    from student_pilot.p3_provenance import pinned, file_pin, source_files, load
    from student_pilot.source_seal import create, binding
    from launch_r1 import entry, production_proof as Q
    from rv import sync_preparation
    syn = J.load(L/'work/build24/proofs/capacity/TWIN_BOUNDARY.json')['pins']
    Twins.ROWS=syn['rows']['sha256']; Twins.BINDING=syn['binding']['sha256']
    Twins.ALIASES=syn['aliases']['sha256']; Rooms.STORE=syn['source_database']['sha256']
    cfg = J.load(OLD/'v.json'); original = deepcopy(cfg)
    request = J.load(OLD/'r.json')
    cfg['r1_training'].pop('host_receipt', None); cfg['r1_training'].pop('review', None)
    cfg.pop('authorization', None); cfg.pop('admission', None)
    cfg['output'] = str(NS/'train'); cfg['r1_training']['stop_after_step'] = 6
    source = L/'work/tree_r1'; control = read(kit/'k/a.json')
    closure = {str(p.relative_to(source)):sha(p) for p in source_files([source/'student_pilot/carrier_c1_run.py'])}
    code = create(source, kit/control['source']['path'], closure, {})
    assert code['tree_sha256'] == control['source']['tree_sha256']
    cfg['code'] = J.write(NS/'code.json', code)
    prep = J.load(OLD/'prepared.json')
    with P.scope(request['_paths']), P.scope(cfg['r1_training']['persisted_files']):
        prep.update(r1_training=deepcopy(cfg['r1_training']), trainer_commit=code['commit'], config_sha256=C.identity(cfg))
        prep['source_seal'] = binding(code, prep['config_sha256'])
        prep['component_evidence'] = Components.artifact_status(cfg)
        cfg['preparation'] = J.write(NS/'prepared_seed.json', prep)
        # Recompute native continuation/config identities after the code pin changes.
        cfg = load(pinned(Q.bind_handover(cfg, NS/'handover')))
        prep = load(pinned(cfg['preparation']))
        prep.update(trainer_commit=code['commit'], component_evidence=Components.artifact_status(cfg))
        cfg['preparation'] = J.write(NS/'prepared.json', prep)
        old_result = J.load(D/'rehearsal3/p2/q/RESULT.json')
        result = deepcopy(old_result)
        result['config'] = J.write(NS/'p2/q/config.json', cfg)
        # The row audit is reusable; the frame-host receipt is an explicit CPU boundary.
        host = dict(status='PASS', config_identity=C.identity(cfg), assertions=dict.fromkeys(entry.ASSERTIONS, True),
                    loader_audit=old_result['audit'], scope='CPU frame-host stand-in only; not a native host proof',
                    kit_sha256=J.seal(kit), source_tree_sha256=code['tree_sha256'])
        result['host_receipt'] = J.write(NS/'p2/q/host.json', host)
        result['rehearsal5'] = dict(reused_audit=str(D/'rehearsal3/p2/q/RESULT.json'),
                                   native_canary_rerun=False, host_boundary='synthetic CPU frame host')
        J.write(NS/'p2/q/RESULT.json', result)
        # h.py consumes the freshly pinned host receipt and produces v.json itself.
        command = [sys.executable, '-B', str(kit/'b/h.py'), str(NS/'p2'), str(NS/'v.json')]
        subprocess.run(command, check=True)
        cfg = J.load(NS/'v.json'); value = C.identity(cfg)
        review = dict(verdict='PASS', config_identity=value, scope='CPU fixture only', canary=file_pin(NS/'p2/q/RESULT.json'))
        cfg['r1_training']['review'] = J.write(NS/'review.json', review)
        sync_preparation(cfg, NS, 'prepared_review.json')
        cfg['admission'] = J.write(NS/'admission.json', dict(verdict='PASS', reviewer='cpu-fixture-regression',
                                    config_sha256=value, preparation=cfg['preparation']))
        cfg['authorization'] = J.write(NS/'authorization.json', dict(verdict='GO', new_gpus=0,
                                    config_sha256=value, job_id='b24f_fresh', scope='CPU fixture only'))
        assert entry.admit(cfg) == 0
        C.prepared(cfg, admission=True)
        Components.artifact_binding(cfg, Components.artifact_status(cfg))
        # Verify that host and review refusals remain active.
        bad = deepcopy(cfg); bad['r1_training'].pop('host_receipt')
        try: entry.admit(bad)
        except ValueError as error: assert str(error) == 'R1_HOST_ADMISSION_MISSING'
        else: raise AssertionError('Missing host accepted')
        bad = deepcopy(cfg); bad['r1_training'].pop('review')
        try: entry.admit(bad)
        except ValueError as error: assert str(error) == 'INDEPENDENT_REVIEW_PENDING'
        else: raise AssertionError('Missing review accepted')
        pin = J.write(NS/'v.json', cfg)
        request['config'] = pin; request['staged_pins'] = [pin, cfg['code']]
        J.write(NS/'r.json', request); J.write(NS/'r2.json', request)
        J.write(NS/'n.json', cfg)
        for name in ('rooms.json',): (R/name).write_bytes((OLD/name).read_bytes())
        fields=[]
        def diff(a,b,path):
            if isinstance(a,dict) and isinstance(b,dict):
                for key in sorted(set(a)|set(b)): diff(a.get(key),b.get(key),path+'.'+key)
            elif a != b: fields.append(dict(field=path,before=a,after=b))
        diff(original,cfg,'v.json')
        put(R/'FIXTURE_FIELDS.json', fields)
        put(R/'PREPARED.json', dict(status='PASS', tree=code['tree_sha256'], kit=J.seal(kit), kit_dir=str(kit),
            canary=sha(NS/'p2/q/RESULT.json'), config=pin, native_prepared=True, native_entry_admit=True,
            host_receipt='regenerated CPU frame-host stand-in; native h.py consumer',
            rows_model_donor='reused read-only', distributed_training_executed=False))
        put(R/'STAGES.json', [dict(stage='fixture_preparation',returncode=0,kit=J.seal(kit))])

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('kit',type=Path,nargs='?',default=L/'out/kit_n_go')
    p.add_argument('--inside',action='store_true'); a=p.parse_args(); kit=a.kit.resolve()
    inside(kit) if a.inside else outside(kit)
