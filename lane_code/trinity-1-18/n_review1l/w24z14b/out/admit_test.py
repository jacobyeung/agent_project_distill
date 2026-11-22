"""Bounded, read-only offline admission probe; no success substitutes for missing inputs."""
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

J = Path('/scratch/jjyeung/orch_n30/n_review1l/w24z14b')
BASE = Path('/scratch/jjyeung/orch_n30/n_review1l/w24z12b')
TREE = BASE / 'work/tree_r1c2'
KIT = BASE / 'out/kit_n_go'
SEAL = 'db42866fd9e8d0090276686527e8ebd8837ab2a9401609d81039b8784187f034'
LIMIT = 16_000_000
started = time.monotonic()

class OfflineUnavailable(Exception):
    pass

class Tee:
    def __init__(self, terminal, log): self.terminal, self.log = terminal, log
    def write(self, text):
        self.terminal.write(text); self.log.write(text); self.log.flush()
    def flush(self): self.terminal.flush(); self.log.flush()


def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    config = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if not output.is_relative_to(J) or output == J:
        raise ValueError('OUTPUT_MUST_BE_UNDER_J')
    output.mkdir(parents=True, exist_ok=False)
    log = (output/'admit.log').open('x')
    sys.stdout = Tee(sys.stdout, log); sys.stderr = Tee(sys.stderr, log)
    report = dict(schema='offline-entry-admit-v1', tree=str(TREE), expected_tree_sha256=SEAL,
                  config=str(config), identity=None, branch_taken=None, checks=[], pin_reads=[],
                  full_admit_pass=False, launch_authorized=False, interpreter=sys.executable,
                  mode='native-call-plus-source-extracted-independent-preconditions')
    checks = report['checks']
    locals_for_checks = {}

    def check(name, source, fn):
        row = dict(name=name, source=source)
        print('\nCHECK', name, source, flush=True)
        try:
            result = fn()
            row.update(status='PASS', reason='Executed on real configuration/source/available bytes.')
            if result is not None: row['result'] = result
        except OfflineUnavailable as e:
            row.update(status='NOT_RUN', reason=str(e)); traceback.print_exc()
        except Exception as e:
            status='FAIL'; reason=f'{type(e).__name__}: {e}'
            if str(e).startswith('P_EXPORT_HANDOVER_FILE_REQUIRED:') and 'cfg' in locals_for_checks:
                label=str(e).split(':',1)[1]
                try:
                    v=locals_for_checks['cfg']['r1_training']
                    receipt=provenance.load(provenance.pinned(v['handover_receipt']))
                    pin=receipt.get('pins',{}).get(label)
                    if pin is not None:
                        location=v.get('persisted_files',{}).get(pin['sha256'],pin['path'])
                        if not Path(location).is_file():
                            status='NOT_RUN'; reason='Native persisted closure requires absent original path '+location+' ('+str(e)+'); offline pin map does not rewrite persisted_files.'
                except Exception: pass
            row.update(status=status, reason=reason); traceback.print_exc()
        checks.append(row)
        shown={k:v for k,v in row.items() if k!='result'} if name=='config_parse' else row
        print(json.dumps(shown, sort_keys=True, default=str), flush=True)
        return row

    def unavailable(reason): raise OfflineUnavailable(reason)
    def require(condition, reason):
        if not condition: raise ValueError(reason)

    sys.path.insert(0, str(TREE))
    from student_pilot import p3_provenance as provenance
    from student_pilot.source_seal import inventory

    def seal():
        files = inventory(TREE)
        actual = provenance.digest(files)
        declared = provenance.load(BASE/'out/TREE_SEAL.json')
        require(actual == SEAL == declared['tree_sha256'] and len(files) == declared['files'], 'TREE_SEAL_MISMATCH')
        for kit in ('kit_n', 'kit_n_go'):
            code = provenance.load(BASE/'out'/kit/'k/7.json')
            require(code['files'] == files and code['tree_sha256'] == actual, 'KIT_TREE_SEAL_MISMATCH:'+kit)
        report['tree_sha256'] = actual
        report['source_files'] = {n:files[n] for n in ('launch_r1/entry.py','student_pilot/carrier_c1_run.py','student_pilot/b7_inputs.py','student_pilot/r1_training.py')}
        return dict(files=len(files), tree_sha256=actual)

    if check('tree_seal', 'student_pilot/source_seal.py:16; launch_r1/build.py:37', seal)['status'] != 'PASS':
        return finish(report, output, 1)

    def parse():
        require(config.is_relative_to(Path('/scratch')), 'CONFIG_MUST_BE_LOCAL_SCRATCH')
        require(config.stat().st_size <= LIMIT, 'CONFIG_TOO_LARGE')
        raw = config.read_bytes()
        cfg = json.loads(raw, object_pairs_hook=provenance.unique,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON:'+x)))
        require(isinstance(cfg, dict), 'CONFIG_MUST_BE_OBJECT')
        report['config_sha256'] = hashlib.sha256(raw).hexdigest()
        report['config_bytes'] = len(raw)
        return cfg

    parsed = check('config_parse', 'student_pilot/p3_provenance.py:23-34', parse)
    cfg = parsed.pop('result', None)
    if cfg is None: return finish(report, output, 1)
    report['branch_taken'] = 'b7' if cfg.get('b7_inputs') else 'legacy_C_prime'
    report['processor_fields'] = {k:cfg.get(k) for k in ('b7_inputs','min_pixels','max_pixels','frame_count','frame_layout','frame_markers')}
    locals_for_checks['cfg']=cfg
    original = copy.deepcopy(cfg)
    report['input_pins'] = []
    def catalog(value, key='cfg'):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value:
                report['input_pins'].append(dict(field=key, path=value['path'], sha256=value['sha256']))
            for k,v in value.items(): catalog(v,key+'.'+k)
        elif isinstance(value,list):
            for i,v in enumerate(value): catalog(v,key+'['+str(i)+']')
    catalog(cfg)
    # Optional map supplies real relocated bytes only. Native pinned() still verifies their hashes.
    offline = {}
    def kit_metadata():
        staging_path=KIT/'k/s.json'
        manifest={n:h for h,n in (line.split('  ',1) for line in (KIT/'SHA256SUMS.txt').read_text().splitlines())}
        require(sha(staging_path)==manifest['k/s.json'],'KIT_STAGING_CAPSULE_CHANGED')
        staging=provenance.load(staging_path)
        folder=output/'kit_metadata'; folder.mkdir()
        total=0; records=[]
        for name,item in staging['entries'].items():
            if 'payload' not in item: continue
            raw=base64.b64decode(item['payload'],validate=True)
            total+=len(raw)
            require(len(raw)<=LIMIT and total<=32_000_000,'KIT_METADATA_TOO_LARGE')
            h=hashlib.sha256(raw).hexdigest()
            require(h==item['sha256'],'KIT_INLINE_PIN_DIFFERS')
            target=folder/h; target.write_bytes(raw); offline[h]=str(target)
            records.append(dict(member=name,sha256=h,bytes=len(raw),local_path=str(target)))
        report['kit_metadata']=dict(source=str(staging_path),sha256=sha(staging_path),records=records)
        return records
    if check('kit_inline_metadata','kit_n_go/k/s.json; SHA256SUMS.txt',kit_metadata)['status']!='PASS':
        return finish(report,output,1)
    map_path = config.parent/'offline_pins.json'
    if map_path.is_file():
        def read_map():
            require(map_path.stat().st_size <= LIMIT, 'OFFLINE_MAP_TOO_LARGE')
            obj = provenance.load(map_path)
            require(isinstance(obj,dict), 'OFFLINE_MAP_MUST_BE_OBJECT')
            for h, p in obj.items():
                require(isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h), 'OFFLINE_MAP_HASH_INVALID')
                require(isinstance(p,str) and Path(p).is_absolute() and Path(p).resolve().is_relative_to(Path('/scratch')), 'OFFLINE_MAP_PATH_INVALID')
            offline.update(obj)
            report['offline_map'] = dict(path=str(map_path), sha256=sha(map_path), entries=len(obj))
        if check('offline_map', 'admit_test.py: optional SHA256-to-local-path map', read_map)['status'] != 'PASS':
            return finish(report, output, 1)

    from student_pilot import r1_persisted
    native_pin = provenance.pinned
    read_budget = [0]
    def local_file(path):
        path = Path(path)
        if not path.is_absolute(): raise OfflineUnavailable('Unstaged relative path: '+str(path))
        if not path.resolve().is_relative_to(Path('/scratch')):
            raise OfflineUnavailable('Remote/job/NFS path outside allowed offline scratch inputs: '+str(path))
        if not path.is_file(): raise OfflineUnavailable('Offline bytes absent: '+str(path))
        if path.stat().st_size > LIMIT: raise OfflineUnavailable('Requires separately authorized bulk IO (>16 MB): '+str(path))
        return path

    def guarded_pin(pin):
        if not isinstance(pin,dict) or set(pin) != {'path','sha256'}:
            return native_pin(pin)  # Preserve the native malformed-pin failure.
        resolved = r1_persisted.relocated(pin)
        path = local_file(resolved)
        row = dict(pin=pin, resolved=str(path))
        report['pin_reads'].append(row)
        result = native_pin(pin)
        row['sha256_verified'] = True
        return result
    provenance.pinned = guarded_pin
    r1_persisted.pinned = guarded_pin
    # Other native modules import the guarded IO boundary, not replacement validators.
    try:
        from student_pilot.carrier_c1_run import identity
        from student_pilot import r1_training, r1_coverage
        from student_pilot.b7_inputs import layout
        from launch_r1 import entry
    except Exception as error:
        check('native_imports', 'student_pilot/carrier_c1_run.py:23-35', lambda: (_ for _ in ()).throw(error))
        return finish(report, output, 1)
    import torch
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    report['runtime'] = dict(nice=os.getpriority(os.PRIO_PROCESS,0), torch_threads=torch.get_num_threads(),
                             torch_interop_threads=torch.get_num_interop_threads(), cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                             virtual_memory_limit=resource.getrlimit(resource.RLIMIT_AS)[0])

    # A Python audit hook forbids native writes, process/network launches and large reads.
    # Imports stay available from the interpreter's installed libraries and the sealed tree.
    library_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), TREE.resolve()]
    def audit(event, args):
        if event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn') or event.startswith('socket.'):
            raise RuntimeError('OFFLINE_SIDE_EFFECT_FORBIDDEN:'+event)
        if event in ('os.remove','os.rmdir','os.rename','os.mkdir','os.chmod','os.link','os.symlink'):
            raise RuntimeError('OFFLINE_MUTATION_FORBIDDEN:'+event)
        if event == 'open' and isinstance(args[0], (str,bytes,os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1], args[2]
            writing = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if writing:
                if path not in (output/'ADMIT.json', output/'admit.log'):
                    raise RuntimeError('OFFLINE_WRITE_FORBIDDEN:'+str(path))
                return
            if any(path.is_relative_to(root) for root in library_roots): return
            if str(path).startswith(('/home/','/data/','/data2/','/data3/')):
                raise OfflineUnavailable('NFS read not authorized for this probe: '+str(path))
            if path.is_file():
                size = path.stat().st_size
                if size > LIMIT or read_budget[0]+size > 128_000_000:
                    raise OfflineUnavailable('Bounded offline IO limit: '+str(path))
                read_budget[0] += size
    sys.addaudithook(audit)

    ns = dict(entry.__dict__, cfg=cfg, value=cfg.get('r1_training',{}), identity=identity, layout=layout,
              validate=r1_training.validate, training_components=r1_training.training_components,
              start=r1_training.start, boundary=r1_training.boundary,
              init_policy=r1_persisted.init_policy, export_only=r1_persisted.export_only)
    entry_ast = ast.parse((TREE/'launch_r1/entry.py').read_text())
    admit_ast = next(n for n in entry_ast.body if isinstance(n,ast.FunctionDef) and n.name=='admit')
    validate_ast = next(n for n in ast.parse((TREE/'student_pilot/r1_training.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate')
    def segment(name, lo, hi, *, function=admit_ast, source='launch_r1/entry.py', pre=None):
        nodes = [n for n in function.body if lo <= n.lineno <= hi]
        if not nodes: raise RuntimeError('EMPTY_SOURCE_SEGMENT')
        def run():
            if pre: pre()
            package=ns['__package__']
            ns['__package__']='student_pilot' if source.startswith('student_pilot/') else 'launch_r1'
            try: exec(compile(ast.Module(body=nodes,type_ignores=[]), str(TREE/source), 'exec'),ns)
            finally: ns['__package__']=package
        return check(name, f'{source}:{lo}-{hi}', run)

    def actual_identity():
        value = identity(cfg)
        report['identity'] = value
        # Independent projection verifies the reported value against the native function.
        canonical = copy.deepcopy(cfg)
        for k in ('preparation','admission','authorization','milestone_gate'): canonical.pop(k,None)
        if 'r1_training' in canonical:
            for k in ('host_receipt','review'): canonical['r1_training'].pop(k,None)
        from trace_format.contracts import heading_plane_min, HEADING_PLANE_MIN_DEFAULT
        if canonical.get('contract_epoch',True): canonical['heading_plane_min']=heading_plane_min(canonical.get('heading_plane_min',HEADING_PLANE_MIN_DEFAULT))
        else: canonical.pop('heading_plane_min',None)
        if 'readout' in canonical: canonical['readout'].pop('contiguous_clips',None)
        if canonical.get('frame_layout')=='spread': canonical.pop('frame_layout')
        require(provenance.digest(canonical)==value,'CONFIG_IDENTITY_DIFFERENT')
        return value
    check('config_identity', 'student_pilot/carrier_c1_run.py:38-52', actual_identity)
    def reference_identity():
        p=config.parent/'identity.txt'
        if not p.is_file(): unavailable('No companion identity.txt; computed identity is not a published-identity witness.')
        local_file(p)
        expected=p.read_text().strip()
        require(expected==report['identity'],'PUBLISHED_CONFIG_IDENTITY_DIFFERS')
        return dict(path=str(p),sha256=sha(p),identity=expected)
    check('published_identity', 'kit_n_go/b/rv.py:251-257', reference_identity)

    paths = {**cfg.get('r1_training',{}).get('persisted_files',{}), **offline}
    def trace(frame,event,arg):
        if event=='line' and frame.f_code.co_filename==str(TREE/'launch_r1/entry.py') and frame.f_code.co_name=='admit':
            report.setdefault('native_admit_lines',[]).append(frame.f_lineno)
            print('NATIVE_ADMIT_LINE',frame.f_lineno)
        return trace
    def native_admit():
        sys.settrace(trace)
        try: return entry.admit(cfg)
        finally: sys.settrace(None)

    with r1_persisted.scope(paths):
        row=check('native_admit', 'launch_r1/entry.py:61-114', native_admit)
        report['full_admit_pass']=row['status']=='PASS'
        segment('deferred_metadata',62,63)
        check('deferred_inline','student_pilot/r1_coverage.py:18-92',lambda:r1_coverage.deferred(cfg))
        segment('init_policy',64,66)
        segment('handover_receipt',67,72)
        check('coverage_and_removal_binding','student_pilot/r1_coverage.py:175-193',lambda:r1_coverage.validate_binding(cfg))
        segment('recipe_geometry_frames',72,85,function=validate_ast,source='student_pilot/r1_training.py')
        segment('mix_and_camera_weights',86,94,function=validate_ast,source='student_pilot/r1_training.py')
        segment('stop_and_milestones',95,99,function=validate_ast,source='student_pilot/r1_training.py')
        processor=segment('processor_legacy_or_b7',78,86)
        report['processor_execution']=dict(mode='exact AST node extracted from sealed admit, with native imports and layout',
            source='launch_r1/entry.py:78-86', status=processor['status'],
            reached_by_full_native_call=any(78<=n<=86 for n in report.get('native_admit_lines',[])))
        if processor['status']=='PASS':
            from student_pilot.pose_samples import DEFAULT_PIXELS
            report['effective_processor_layout']=layout(cfg if cfg.get('b7_inputs') else dict(cfg,min_pixels=DEFAULT_PIXELS[0],max_pixels=DEFAULT_PIXELS[1],frame_count=cfg.get('frame_count',32)))
        check('expected_N_legacy_branch','launch_r1/entry.py:78-86',lambda:require(not cfg.get('b7_inputs'),'N_LEGACY_BRANCH_EXPECTED'))
        segment('all_stream_identities',87,89)
        segment('continuation_boundary',90,91)
        segment('training_components',92,92)
        segment('row_plan_present',93,94)
        segment('sampler_binding',95,95,pre=lambda:ns.update(validate_binding=__import__('student_pilot.r1_mix',fromlist=['validate_binding']).validate_binding))
        segment('row_plan_digest',96,97)
        host=segment('host_receipt_pin',98,98)
        if host['status']=='PASS': segment('host_receipt_assertions',100,103)
        else: check('host_receipt_assertions','launch_r1/entry.py:100-103',lambda:unavailable('Host receipt bytes unavailable; see host_receipt_pin.'))
        review=segment('review_receipt_pin',99,99)
        if review['status']=='PASS': segment('review_verdict_identity',112,113)
        else: check('review_verdict_identity','launch_r1/entry.py:112-113',lambda:unavailable('Review receipt bytes unavailable; see review_receipt_pin.'))
        def need_host():
            if host['status']!='PASS' and not r1_coverage.deferred(cfg): unavailable('Routing counts require missing host receipt.')
        segment('routing_card_and_counts',104,111,pre=need_host)
        # start and component validation can also read persisted paths directly.
        # Refuse unavailable closures before direct Path.is_file checks mislabel them as bad bytes.
        def start():
            value=cfg.get('r1_training',{})
            if value.get('handover_receipt'):
                receipt=provenance.load(guarded_pin(value['handover_receipt']))
                for label,pin in receipt.get('pins',{}).items():
                    if label in ('artifact','config','binding','preparation') or label.startswith(('stream/','indices/')):
                        local_file(value.get('persisted_files',{}).get(pin['sha256'],pin['path']))
            return r1_training.start(cfg)
        check('initialization_start','launch_r1/entry.py:114; student_pilot/r1_training.py:135-161',start)
        def preparation_identity():
            if not cfg.get('preparation'): unavailable('Preparation receipt has not been supplied/built.')
            prep=provenance.load(guarded_pin(cfg['preparation']))
            require(prep.get('config_sha256')==report['identity'],'PREPARATION_CONFIG_IDENTITY_DIFFERS')
            return prep['config_sha256']
        check('preparation_identity','kit_n_go/b/rv.py:232-236; carrier_c1_run.py:38',preparation_identity)
        def census_pin():
            if host['status']!='PASS': unavailable('Host receipt unavailable; cannot read protected_census pin.')
            if not cfg.get('remove_files'): return 'Not applicable: no remove_files.'
            pin=ns.get('host',{}).get('protected_census')
            if not pin: unavailable('Host receipt has no protected_census pin.')
            value=provenance.load(guarded_pin(pin))
            require(value.get('config_identity')==report['identity'],'R1_CENSUS_IDENTITY_DIFFERS')
            return dict(pin=pin,note='Pin and identity only; full cs.verify remains separate.')
        check('protected_census_pin_identity','kit_n_go/b/h.py:30-35; b/rv.py:265-271; b/cs.py:161-166',census_pin)

    check('full_census_verification','kit_n_go/b/cs.py:157-207',lambda:unavailable('Needs original job root p/q/host.json, p/i/staging.json, p/q/ss.json, c5.json, live/c4.json, protected-key files, staged source pins and SLURM_JOB_ID/location. v.json alone supplies none of this layout; no job root is fabricated.'))
    check('caller_staging_verification','kit_n_go/b/u.py:16-19; launch_r1/production_proof.py:10-14',lambda:unavailable('Needs original r.json staged_pins and _paths plus staged files; absent from the two-argument v.json interface.'))
    check('caller_prepared_config_equality','kit_n_go/b/u.py:7-14',lambda:unavailable('Needs original q/RESULT.json and its authenticated config pin; identity.txt and preparation checks are separate.'))
    check('input_unchanged','admit_test.py: input invariance',lambda:require(cfg==original and sha(config)==report['config_sha256'],'INPUT_MUTATED'))
    # Only source files were read; the audit hook forbids any mutation of the tree/kits.
    failed=any(r['status']=='FAIL' for r in checks)
    return finish(report,output,1 if failed else 0)


def finish(report,output,rc):
    report['exit_code']=rc
    report['status']='FAIL' if rc else ('PASS_OFFLINE_PARTIAL' if any(r['status']=='NOT_RUN' for r in report['checks']) else 'PASS')
    report['elapsed_seconds']=round(time.monotonic()-started,3)
    report['max_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    print('\nSUMMARY',json.dumps({k:report[k] for k in ('status','identity','branch_taken','full_admit_pass','exit_code','elapsed_seconds')},sort_keys=True))
    (output/'ADMIT.json').write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+'\n')
    return rc

if __name__=='__main__':
    raise SystemExit(main())
