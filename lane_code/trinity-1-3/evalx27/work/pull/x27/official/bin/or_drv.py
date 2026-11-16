#!/usr/bin/env python3
"""Official reads driver (lane official_reads). Runs inside or_job.sh's bwrap (container path /project/community/jjyeung/distill).

  run --plan PLAN.json     stage the P1 evaluator tree and the models, then run each phase of PLAN in order
  dry --plan PLAN.json     login-node check of inputs and pins (no staging, no GPU)

PLAN: {"phases": [{"cell": NAME, "model": "f17" | "/path/milestone_N.tar", "bench": "vsti450" | "vsi5130"}, ...]}
Each phase = one official/run_eval_hc.py call with --launch_workers 4 (one worker per GPU, scene-partitioned shards that
flush every item), then official/score_and_aggregate.py. Outputs: runs/CELL/ (shard_*.jsonl, predictions.jsonl,
protocol.json, worker logs), scores/CELL/, runs/CELL/DONE.json. A phase with DONE.json is skipped; a phase with partial
shards resumes (the harness skips finished ids). STOP file or SIGTERM: workers are killed and the driver exits 0 (stopped).
Publications and models sit at fixed node-local paths so a resumed job (any node) has the same config_sha256."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

J = '/project/community/jjyeung'
O = J + '/official_reads'
K = J + '/p1_rt'
P = J + '/distill'
RR = 'runs/aws128p_20261025'
PE = 'data2root/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/eval_instructed_provisional_e3e9ffb/artifacts/paper_eval'
VSTI_REL = PE + '/vstibench_repr450_v3/prepared'
SNAPSHOT = P + '/' + RR + '/models/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
VENV_PY = P + '/venvs/rwtrain_torch211_cu129/bin/python'
F17_PUB = P + '/' + RR + '/r1d_8d19426a/attempt-8608561-0/publication'
VIDEO_ROOT = P + '/data2root/jjyeung/agent_project_data/vsibench_videos'
META = J + '/cp4tk_eval/official/meta_5130.jsonl'
R_TAR = K + '/reads/in/r.tar'
NODE = '/tmp/jjy_or'
NG = 4
MAXTOK = 8192
PINS = {R_TAR: '31fcfc3b0e4042416f98530bf2c6909b9d0c510945e5b06fa0cee00f5e644ffe',
        META: 'd69dfb86e94cbb9821b8b2abe5a94b32cf69a9430d3ca3f482154afe45786abc'}
TREE_PINS = {'official/run_eval_hc.py': '7a7416451ec42f954ff94d600bb4657a6995f6a94400a8f104c8f6b97d5c82b8',
             'official/score_and_aggregate.py': '0bb536ca2eb60eaee54c2f18ed93103a41ff61db1bcbec1c36e5273f3b1ef2a1'}
VSTI_PINS = {'generation/manifest.json': '7167390bec007be66c4b2a55eecf08838394221fcddfaf4cefe70b86999ee947',
             'generation/inputs.jsonl': '07f99629336b1f3c607edc1d0bee308b86f89fd0f23b8775471f1016a78758cf',
             'generation/media.json': '49c24be547ad3181cba0bbc84af8ee4bb6fc25ed6931765a5a128482b7e4367c',
             'scoring/labels.jsonl': 'd97d71379111815c315c6c40dfe07f3beb081611f1e332e338c9c50f112cc44f',
             'scoring/manifest.json': '1c35feb7dc597379c0983e922dcc46975d3dbf99dd246188cdf19e48e33d75d2'}
F17_PINS = {'adapter-ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW/full_weights/full_weights.json':
            'fafcbef1960681e12b51fbdce2e000a0c158400dbcc79d1090c3848cf0db35cf',
            'auxiliary_heads.pt': '8ffb71a93e5706e48c767edfcc8d6c301f9b4de1124fe094e48d7a2e51bae162'}
BENCH = {'vsti450': {'expected': 450, 'score_mode': 'our_cell', 'benchmark': 'vstibench_repr450_v3'},
         'vsi5130': {'expected': 5130, 'score_mode': 'official_full', 'benchmark': 'vsibench_full'}}
JOB = os.environ.get('SLURM_JOB_ID', 'nojob')
T0 = time.time()
STATUS = {'job': JOB, 'host': os.uname()[1], 'phases': {}}
STOP_FLAG = {'why': None}
CHILD = {'p': None}
LOG = None


def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def say(msg):
    line = '%s +%5.0fs %s\n' % (stamp(), time.time() - T0, msg)
    sys.stdout.write(line)
    sys.stdout.flush()
    if LOG:
        LOG.write(line)
        LOG.flush()


def write_json(path, obj):
    tmp = os.path.join(os.path.dirname(path), '.' + os.path.basename(path) + '.tmp.%s' % JOB)
    with open(tmp, 'w') as f:
        f.write(json.dumps(obj, indent=1, sort_keys=True))
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(16 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check_pins(base, pins):
    bad = {}
    for rel, want in sorted(pins.items()):
        p = os.path.join(base, rel) if base else rel
        got = sha256_file(p) if os.path.isfile(p) else 'missing'
        if got != want:
            bad[rel] = got
    return bad


def run(cmd, **kw):
    say('RUN ' + ' '.join(str(c) for c in cmd)[:400])
    subprocess.check_call([str(c) for c in cmd], **kw)


def model_key(model):
    if model == 'f17':
        return 'f17'
    base = os.path.basename(model)
    if not (base.startswith('milestone_') and base.endswith('.tar')):
        raise ValueError('model must be f17 or /path/milestone_N.tar: %r' % model)
    run_name = os.path.basename(os.path.dirname(os.path.dirname(model)))
    return '%s_%d' % (run_name, int(base[len('milestone_'):-len('.tar')]))


# ---------------------------------------------------------------- staging (fixed node-local paths)
def stage_tree():
    """P1 evaluator tree at NODE/r_<sha12>, extracted once per node."""
    tree = os.path.join(NODE, 'r_' + PINS[R_TAR][:12])
    ok = tree + '.ok'
    if not os.path.isfile(ok):
        if os.path.exists(tree):
            os.rename(tree, tree + '.partial.%d' % int(time.time()))
        os.makedirs(tree)
        run(['tar', '-xf', R_TAR, '-C', tree])
        bad = check_pins(tree, TREE_PINS)
        if bad:
            raise RuntimeError('evaluator tree pins differ: %r' % bad)
        open(ok, 'w').write(stamp())
    return tree


def lite_publication(ms_dir, pub):
    """Deterministic publication of a milestone's own bytes (hard links + the two files the head loader authenticates),
    as the P1 reads kit's lite fallback (p1r.py) with a fixed path, so config_sha256 is stable across jobs and nodes."""
    meta = json.load(open(os.path.join(ms_dir, 'MILESTONE.json')))
    os.makedirs(os.path.join(pub, 'full_weights'))
    for rel in meta['files']:
        if rel.startswith('full_weights/'):
            os.link(os.path.join(ms_dir, rel), os.path.join(pub, rel))
    os.link(os.path.join(ms_dir, 'auxiliary_heads.pt'), os.path.join(pub, 'auxiliary_heads.pt'))
    heads = meta['files']['auxiliary_heads.pt']
    raw = json.load(open(os.path.join(ms_dir, 'auxiliary_heads.json')))
    raw['weights'] = {'path': os.path.join(pub, 'auxiliary_heads.pt'), 'sha256': heads['sha256'], 'bytes': heads['bytes']}
    with open(os.path.join(pub, 'auxiliary_heads.json'), 'w') as f:
        json.dump(raw, f, indent=1, sort_keys=True)
    with open(os.path.join(pub, 'SHA256_MANIFEST.json'), 'w') as f:
        json.dump({'schema': 'p1-read-lite-publication-v1', 'lite': True, 'milestone': ms_dir,
                   'files': {'auxiliary_heads.pt': {'sha256': heads['sha256'], 'bytes': heads['bytes']}}},
                  f, indent=1, sort_keys=True)


def stage_model(model):
    """-> publication path (adapter_dir and heads_dir of the harness)."""
    if model == 'f17':
        bad = check_pins(F17_PUB, F17_PINS)
        if bad:
            raise RuntimeError('f17 publication pins differ: %r' % bad)
        return F17_PUB
    key = model_key(model)
    st = os.stat(model)
    tag = '%s.%d.%d' % (key, st.st_size, int(st.st_mtime))
    root = os.path.join(NODE, 'm', key)
    pub = os.path.join(NODE, 'pub', key)
    ok = os.path.join(NODE, 'm', key + '.ok')
    if os.path.isfile(ok) and open(ok).read().strip() == tag and os.path.isfile(os.path.join(pub, 'SHA256_MANIFEST.json')):
        say('%s: reusing node-local milestone + publication' % key)
        return pub
    for d in (root, pub):
        if os.path.exists(d):
            os.rename(d, d + '.old.%d' % int(time.time()))
    os.makedirs(root)
    run(['tar', '-xf', model, '-C', root])
    names = [n for n in os.listdir(root) if n.startswith('milestone_')]
    if len(names) != 1:
        raise RuntimeError('milestone tar holds %r' % names)
    ms_dir = os.path.join(root, names[0])
    meta = json.load(open(os.path.join(ms_dir, 'MILESTONE.json')))
    want_step = int(os.path.basename(model)[len('milestone_'):-len('.tar')])
    if int(meta.get('step', -1)) != want_step:
        raise RuntimeError('MILESTONE.json step %r != %d' % (meta.get('step'), want_step))
    bad = [rel for rel, pin in sorted(meta['files'].items())
           if not os.path.isfile(os.path.join(ms_dir, rel)) or os.path.getsize(os.path.join(ms_dir, rel)) != pin['bytes']
           or sha256_file(os.path.join(ms_dir, rel)) != pin['sha256']]
    if bad:
        raise RuntimeError('milestone files differ from MILESTONE.json: %r' % bad)
    say('%s: MILESTONE_VERIFY step=%d files=%d bad=0' % (key, want_step, len(meta['files'])))
    os.makedirs(os.path.dirname(pub), exist_ok=True)
    lite_publication(ms_dir, pub)
    with open(ok, 'w') as f:
        f.write(tag)
    return pub


# ---------------------------------------------------------------- phases
def trim_partial_lines(out):
    """A killed worker can leave a partial last line; keep a copy and rewrite the valid prefix (the harness then resumes)."""
    if not os.path.isdir(out):
        return
    for n in sorted(os.listdir(out)):
        if not (n.startswith('shard_') and n.endswith('.jsonl')):
            continue
        p = os.path.join(out, n)
        data = open(p, 'rb').read()
        lines = data.split(b'\n')
        good, bad = [], 0
        for i, ln in enumerate(lines):
            if not ln.strip():
                continue
            try:
                json.loads(ln.decode('utf-8'))
                good.append(ln)
            except ValueError:
                bad += 1
        if bad or (data and not data.endswith(b'\n')):
            keep = p + '.pre_trim.%d' % int(time.time())
            os.rename(p, keep)
            with open(p, 'wb') as f:
                f.write(b''.join(g + b'\n' for g in good))
            say('trimmed %s: %d valid lines, %d bad (copy %s)' % (p, len(good), bad, keep))


def count_lines(out):
    n = 0
    if os.path.isdir(out):
        for name in os.listdir(out):
            if name.startswith('shard_') and name.endswith('.jsonl'):
                with open(os.path.join(out, name), 'rb') as f:
                    n += sum(1 for ln in f if ln.strip())
    return n


def harness_cmd(tree, ph, pub, out):
    cmd = [VENV_PY, '-I', os.path.join(tree, 'official', 'run_eval_hc.py'), '--arch', 'q35', '--prompt_mode', 'ours',
           '--thinking', 'on', '--max_new_tokens', MAXTOK, '--max_frames_num', 32, '--model_dir', SNAPSHOT,
           '--adapter_dir', pub, '--headcall', 'own', '--heads_dir', pub, '--video_root', VIDEO_ROOT,
           '--data2_root', P + '/data2root', '--output_dir', out, '--num_shards', NG, '--launch_workers', NG]
    if ph['bench'] == 'vsti450':
        cmd += ['--dataset_mode', 'prepared_cell', '--frame_source', 'prepared_32', '--prepared_dir', P + '/' + VSTI_REL]
    else:
        cmd += ['--dataset_mode', 'official_full', '--frame_source', 'video_32', '--meta_jsonl', META]
    return cmd


def env_for(tree):
    env = dict(os.environ)
    jd = os.path.join(NODE, 'jd_' + JOB)
    for d in ('tmp', 'hf', 'cache', 'triton', 'home', 'torch', 'inductor'):
        os.makedirs(os.path.join(jd, d), exist_ok=True)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               HF_HOME=os.path.join(jd, 'hf'), XDG_CACHE_HOME=os.path.join(jd, 'cache'),
               TRITON_CACHE_DIR=os.path.join(jd, 'triton'), TMPDIR=os.path.join(jd, 'tmp'), HOME=os.path.join(jd, 'home'),
               TORCH_HOME=os.path.join(jd, 'torch'), TORCHINDUCTOR_CACHE_DIR=os.path.join(jd, 'inductor'),
               TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
    return env


def stop_child(why):
    if STOP_FLAG['why'] is None:
        STOP_FLAG['why'] = why
    p = CHILD['p']
    if p is not None and p.poll() is None:
        say('stopping harness (%s): TERM to process group %d' % (why, p.pid))
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(30):
            if p.poll() is not None:
                break
            time.sleep(1)
        if p.poll() is None:
            say('harness still alive after 30 s: KILL')
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass


def on_term(signum, frame):
    stop_child('signal %d' % signum)


def run_phase(tree, ph, env):
    cell, bench = ph['cell'], BENCH[ph['bench']]
    out = os.path.join(O, 'runs', cell)
    sc = os.path.join(O, 'scores', cell)
    st = STATUS['phases'].setdefault(cell, {})
    if os.path.isfile(os.path.join(out, 'DONE.json')):
        st.update(state='done_before')
        say('%s: DONE.json exists, skipping' % cell)
        return True
    pub = stage_model(ph['model'])
    os.makedirs(out, exist_ok=True)
    os.makedirs(sc, exist_ok=True)
    trim_partial_lines(out)
    before = count_lines(out)
    st.update(state='running', model=ph['model'], publication=pub, items_before=before, expected=bench['expected'],
              start=stamp())
    write_json(os.path.join(O, 'status.json'), STATUS)
    log = open(os.path.join(O, 'logs', 'harness_%s_%s.log' % (cell, JOB)), 'a')
    cmd = harness_cmd(tree, ph, pub, out)
    say('%s: start (%d/%d items already done) %s' % (cell, before, bench['expected'], ' '.join(map(str, cmd))[:600]))
    CHILD['p'] = subprocess.Popen([str(c) for c in cmd], env=env, cwd=tree, stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
    last = 0
    while CHILD['p'].poll() is None:
        time.sleep(5)
        if os.path.isfile(os.path.join(O, 'STOP')):
            stop_child('STOP file')
        if time.time() - last >= 60:
            last = time.time()
            st.update(items=count_lines(out), t=stamp())
            write_json(os.path.join(O, 'status.json'), STATUS)
    rc = CHILD['p'].returncode
    CHILD['p'] = None
    log.close()
    st.update(items=count_lines(out), harness_rc=rc, t=stamp())
    if STOP_FLAG['why']:
        st.update(state='stopped', why=STOP_FLAG['why'])
        say('%s: stopped (%s) at %d/%d items' % (cell, STOP_FLAG['why'], st['items'], bench['expected']))
        return False
    if rc != 0:
        st.update(state='failed')
        say('%s: harness rc %d' % (cell, rc))
        return False
    score_cmd = [VENV_PY, '-I', os.path.join(tree, 'official', 'score_and_aggregate.py'), '--mode', bench['score_mode'],
                 '--input', out, '--results_dir', sc, '--cell_name', cell, '--expected_count', bench['expected']]
    if bench['score_mode'] == 'official_full':
        score_cmd += ['--output_dir', sc]
    else:
        score_cmd += ['--benchmark', bench['benchmark']]
    with open(os.path.join(sc, 'score_stdout.json'), 'w') as f:
        src = subprocess.call([str(c) for c in score_cmd], env=env, cwd=tree, stdout=f,
                              stderr=open(os.path.join(sc, 'score_stderr.log'), 'w'))
    st.update(score_rc=src)
    try:
        st['score'] = json.load(open(os.path.join(sc, 'score_stdout.json')))
        st['score'].pop('scored_records', None)
    except ValueError:
        st['score'] = None
    write_json(os.path.join(out, 'DONE.json'), {'cell': cell, 'model': ph['model'], 'publication': pub, 'job': JOB,
                                                'items': st['items'], 'harness_rc': rc, 'score_rc': src, 't': stamp()})
    st.update(state='done' if src == 0 else 'scored_failed')
    say('%s: done, score rc %d' % (cell, src))
    return True


def load_plan(path, require_tars=True):
    plan = json.load(open(path))
    for ph in plan['phases']:
        if ph['bench'] not in BENCH or not ph['cell'].replace('_', '').isalnum():
            raise ValueError('bad phase %r' % ph)
        if require_tars and ph['model'] != 'f17' and not os.path.isfile(ph['model']):
            raise ValueError('milestone tar missing: %s' % ph['model'])
        model_key(ph['model'])
    return plan


def main_run(a):
    global LOG
    os.makedirs(os.path.join(O, 'logs'), exist_ok=True)
    LOG = open(os.path.join(O, 'logs', 'driver_%s.log' % JOB), 'a')
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    plan = load_plan(a.plan)
    STATUS.update(plan=a.plan, start=stamp(), state='staging')
    bad = check_pins(None, PINS)
    if bad:
        raise RuntimeError('input pins differ: %r' % bad)
    if check_pins(P + '/' + VSTI_REL, VSTI_PINS):
        raise RuntimeError('VSTI v3 prepared pins differ: %r' % check_pins(P + '/' + VSTI_REL, VSTI_PINS))
    tree = stage_tree()
    env = env_for(tree)
    probe = subprocess.check_output([VENV_PY, '-c', 'import torch,transformers;print(torch.__version__,'
                                     'transformers.__version__,torch.cuda.device_count())'], env=env, cwd=tree).decode()
    say('venv probe: ' + probe.strip())
    STATUS.update(state='running', venv=probe.strip(), tree=tree)
    ok = True
    for ph in plan['phases']:
        if STOP_FLAG['why'] or os.path.isfile(os.path.join(O, 'STOP')):
            STOP_FLAG['why'] = STOP_FLAG['why'] or 'STOP file'
            break
        try:
            ok = run_phase(tree, ph, env) and ok
        except Exception as error:
            STATUS['phases'].setdefault(ph['cell'], {}).update(state='failed', error=repr(error))
            say('%s: FAILED %r' % (ph['cell'], error))
            ok = False
        write_json(os.path.join(O, 'status.json'), STATUS)
    STATUS.update(state='stopped' if STOP_FLAG['why'] else ('done' if ok else 'done_with_failures'), end=stamp())
    write_json(os.path.join(O, 'status.json'), STATUS)
    if STOP_FLAG['why']:
        write_json(os.path.join(O, 'STOPPED_%s.json' % JOB), {'why': STOP_FLAG['why'], 't': stamp(), 'phases': STATUS['phases']})
        say('STOPPED (%s); resubmit the same plan to finish' % STOP_FLAG['why'])
        return 0
    return 0 if ok else 1


def main_dry(a):
    plan = load_plan(a.plan, require_tars=False)
    rep = {'plan': plan, 'pins_bad': check_pins(None, PINS), 'stop_file': os.path.isfile(os.path.join(O, 'STOP'))}
    import tarfile
    with tarfile.open(R_TAR) as tf:
        names = set(tf.getnames())
        rep['tree_has'] = {n: ('./' + n in names or n in names) for n in TREE_PINS}
    rep['vsti_src_bad'] = check_pins(J + '/q7e/stage/distill/' + VSTI_REL, VSTI_PINS)
    rep['meta_lines'] = sum(1 for _ in open(META))
    for ph in plan['phases']:
        out = os.path.join(O, 'runs', ph['cell'])
        rep.setdefault('phases', []).append({'cell': ph['cell'], 'key': model_key(ph['model']),
                                             'tar_present': ph['model'] == 'f17' or os.path.isfile(ph['model']),
                                             'done': os.path.isfile(os.path.join(out, 'DONE.json')),
                                             'items_so_far': count_lines(out)})
    print(json.dumps(rep, indent=1, sort_keys=True))
    return 0 if not rep['pins_bad'] and not rep['vsti_src_bad'] and all(rep['tree_has'].values()) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd')
    for name in ('run', 'dry'):
        s = sub.add_parser(name)
        s.add_argument('--plan', required=True)
    a = ap.parse_args()
    if a.cmd == 'run':
        sys.exit(main_run(a))
    if a.cmd == 'dry':
        sys.exit(main_dry(a))
    ap.print_help()
    sys.exit(2)


if __name__ == '__main__':
    main()
