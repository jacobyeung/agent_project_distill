"""Tests for launch.py: job names, prepare's refusals, submit's gates, the template and a local run."""
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import anon, launch, ledger, pack, util  # noqa: E402

HERE = os.path.join(TOOLS, 'orchkit')
REF = '/scratch/jjyeung/distill_sync/stage'
READK_LAUNCHER = REF + '/trinity-1-3/cont_ops/work/d0/readk/kit/launcher/orchard_launcher.py'
TREE_JOBS = '/scratch/jjyeung/orch_n30/eff_audit/repo/sealed_tree_b01ce449/launch_s1/b'


def write(path, data, mode=None):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))
    if mode:
        os.chmod(path, mode)


def sbatch_lines(script):
    out = {}
    for line in script.splitlines():
        if line.startswith('#SBATCH'):
            for part in re.findall(r'(--?[A-Za-z-]+)[= ]?(\S*)', line[len('#SBATCH'):]):
                out[part[0]] = part[1]
    return out


def fake_provenance(checkout, config_path):
    return {'repo_commit': 'f' * 40, 'checkout': checkout, 'dirty': False,
            'config_sha256': util.sha256_file(config_path)[0]}


class LaunchBase(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix='orchkit_launch_')
        self.saved = dict((key, os.environ.get(key)) for key in ('ORCHKIT_LEDGER', 'ORCHKIT_OSSH',
                                                                 'ORCHKIT_ANON_WORDS'))
        self.ledger = os.path.join(self.base, 'ledger.jsonl')
        os.environ['ORCHKIT_LEDGER'] = self.ledger
        os.environ['ORCHKIT_OSSH'] = os.path.join(self.base, 'fake_ossh.sh')
        write(os.path.join(self.base, 'bin', 'sbatch'),
              '#!/bin/bash\necho "$@" >> %s/sbatch_calls\nfor a in "$@"; do [ "$a" = --test-only ]'
              ' && exit 0; done\necho 4242\n' % self.base, 0o755)
        write(os.environ['ORCHKIT_OSSH'],
              '#!/bin/bash\necho call >> %s/ossh_calls\nexport HOME=%s/home PATH=%s/bin:$PATH\n'
              '[ "$1" = "bash -s" ] || exit 9\nexec bash -s\n' % (self.base, self.base, self.base),
              0o755)
        write(os.path.join(self.base, 'bin', 'squeue'),
              '#!/bin/bash\ncat %s/live 2>/dev/null || true\n' % self.base, 0o755)
        os.makedirs(os.path.join(self.base, 'home'))
        os.makedirs(os.path.join(self.base, 'pool'))
        words = os.path.join(self.base, 'words.txt')
        write(words, 'text zzqqxxnever\n')
        self.loose = anon.load_rules(words)
        os.environ['ORCHKIT_ANON_WORDS'] = words
        self.count = 0

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def config(self, **job):
        value = {'schema': 'orchkit-config-v1', 'family': 'generic', 'kit_pins_sha256': '0' * 64,
                 'job': {'partition': 'general', 'gpus': 0, 'cpus': 1, 'mem_gb': 1,
                         'time_limit_s': 600, 'signal_s': 60, 'nice': 0,
                         'root_parent': os.path.join(self.base, 'nodetmp')},
                 'entry': ['python3', '{kit}/code/entry.py', '{out}'], 'n_items': 1,
                 'budgets': {'return': {'max_bytes': 10 ** 7}, 'pool': {'max_bytes': 10 ** 6},
                             'home': {'max_bytes': 4096}},
                 'records': [], 'spec': {}, 'stage': [],
                 'return': {'pool': os.path.join(self.base, 'pool')}}
        value['job'].update(job)
        return value

    def kit(self, config=None, entry="import os,sys\nopen(os.path.join(sys.argv[1],'r.txt'),'w').write('ok')\n",
            rules=None):
        self.count += 1
        source = os.path.join(self.base, 'src%d' % self.count)
        write(os.path.join(source, 'entry.py'), entry)
        config_path = os.path.join(self.base, 'cin%d.json' % self.count)
        util.write_json(config_path, config or self.config())
        summary = pack.pack(source, config_path, os.path.join(self.base, 'kit%d' % self.count),
                            rules=rules or self.loose)
        dry = os.path.join(self.base, 'dry%d.json' % self.count)
        util.write_json(dry, {'schema': 'orchkit-dryrun-v1', 'verdict': 'PASS',
                              'kit_pins_sha256': summary['kit_pins_sha256'],
                              'config_sha256': summary['config_sha256']})
        return summary['kit'], dry

    def prepare(self, kit, dry, rules=None, **extra):
        self.count += 1
        args = dict(dryrun=dry, provenance_fn=fake_provenance, rules=rules or self.loose)
        args.update(extra)
        return launch.prepare(kit, os.path.join(kit, 'CONFIG.json'),
                              os.path.join(self.base, 'prep%d' % self.count), 'lane_t',
                              'toy job', '/x/epoch', **args), os.path.join(
                                  self.base, 'prep%d' % self.count)

    def go(self, text):
        self.count += 1
        path = os.path.join(self.base, 'GO%d.md' % self.count)
        write(path, text)
        return path

    def calls(self, name):
        path = os.path.join(self.base, name)
        if not os.path.exists(path):
            return []
        with open(path) as handle:
            return handle.read().splitlines()


class JobNameTest(unittest.TestCase):
    def test_minted_names_match_and_differ(self):
        names = set()
        for _ in range(200):
            token, name = launch.mint_job_name()
            self.assertRegex(name, r'^a15_cot_ap[0-9a-f]{16}$')
            self.assertEqual(name, 'a15_cot_ap' + token)
            names.add(name)
        self.assertEqual(len(names), 200)
        for bad in ('0123', 'ABCDEF0123456789', '0123456789abcdeg', '0123456789abcdef0'):
            with self.assertRaises(launch.LaunchError):
                launch.mint_job_name(bad)


class PrepareTest(LaunchBase):
    def test_prepare_appends_exactly_one_row_and_contacts_nothing(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        rows = ledger.read_rows(self.ledger)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['event'], 'minted')
        self.assertEqual(rows[0]['job_name'], record['job_name'])
        self.assertEqual(rows[0]['kit_pins_sha256'], record['kit_pins_sha256'])
        self.assertEqual(self.calls('ossh_calls'), [])
        self.assertEqual(record['argv'][-1], 'bash -s')
        self.assertEqual(record['argv'][3], os.environ['ORCHKIT_OSSH'])
        self.assertEqual(record['provenance']['repo_commit'], 'f' * 40)
        with open(os.path.join(prep, 'BATCH.sh')) as handle:
            script = handle.read()
        self.assertIn('#SBATCH --job-name=%s' % record['job_name'], script)

    def assertRefused(self, kit, dry, **extra):
        before = len(ledger.read_rows(self.ledger))
        with self.assertRaises(launch.LaunchError) as caught:
            self.prepare(kit, dry, **extra)
        self.assertEqual(len(ledger.read_rows(self.ledger)), before)
        self.assertFalse(os.path.exists(os.path.join(self.base, 'prep%d' % self.count)))
        return str(caught.exception)

    def test_prepare_refuses_missing_failed_or_mismatched_dry_run(self):
        kit, dry = self.kit()
        self.assertIn('no dry-run', self.assertRefused(kit, os.path.join(self.base, 'none.json')))
        report = util.read_json(dry)
        util.write_json(dry, dict(report, verdict='FAIL'))
        self.assertIn('FAIL', self.assertRefused(kit, dry))
        util.write_json(dry, dict(report, config_sha256='1' * 64))
        self.assertIn('differ', self.assertRefused(kit, dry))
        record, _ = self.prepare(kit, None, no_dryrun_reason='toy run, no shims yet')
        self.assertIn('no-dryrun: toy run', ledger.lookup(record['token'], self.ledger)[0]['meaning'])

    def test_prepare_refuses_schema_invalid_config(self):
        kit, dry = self.kit(self.config(partition='nowhere', gpus=-1))
        self.assertIn('config is invalid', self.assertRefused(kit, dry))
        bad = self.config()
        bad['family'] = 'read'
        kit, dry = self.kit(bad)
        self.assertIn('$.spec', self.assertRefused(kit, dry))

    def test_prepare_refuses_an_opacity_hit(self):
        config = self.config()
        config['return']['pool'] = '/project/x/pool'
        config['job']['root_parent'] = '/tmp'
        kit, dry = self.kit(config, entry="MODEL = 'qwen'\n")
        self.assertIn('opacity', self.assertRefused(kit, dry, rules=anon.load_rules(anon.WORDS)))
        kit, dry = self.kit(config)
        record, _ = self.prepare(kit, dry, rules=anon.load_rules(anon.WORDS))
        self.assertRegex(record['job_name'], launch.JOB_NAME.pattern)

    def test_prepare_refuses_a_provenance_refusal(self):
        kit, dry = self.kit()

        def refuse(checkout, config_path):
            raise launch.LaunchError('provenance refused: dirty')

        self.assertIn('provenance', self.assertRefused(kit, dry, provenance_fn=refuse))
        with self.assertRaises(launch.LaunchError):
            launch.provenance('/home/jjyeung/agent_project_distill', os.path.join(kit, 'CONFIG.json'))
        with self.assertRaises(launch.LaunchError):
            launch.provenance('/data2/x', os.path.join(kit, 'CONFIG.json'))

    def test_prepare_refuses_an_unpinned_or_changed_kit_file(self):
        kit, dry = self.kit()
        write(os.path.join(kit, 'code', 'extra.py'), 'pass\n')
        self.assertIn('without a pin', self.assertRefused(kit, dry))
        kit, dry = self.kit()
        write(os.path.join(kit, 'code', 'entry.py'), 'changed\n')
        self.assertIn('pins differ', self.assertRefused(kit, dry))


class SubmitTest(LaunchBase):
    def test_go_must_name_the_token_and_no_execute_makes_no_call(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        with self.assertRaises(launch.LaunchError):
            launch.submit(prep, self.go('GO for some other job 0123456789abcdef\n'))
        with self.assertRaises(launch.LaunchError):
            launch.submit(prep, os.path.join(self.base, 'missing_GO.md'))
        calls = []
        result = launch.submit(prep, self.go('GO %s\n' % record['job_name']), out=io.StringIO(),
                               transport=lambda argv, body: calls.append(argv))
        self.assertFalse(result['executed'])
        self.assertEqual(calls, [])
        self.assertEqual(self.calls('ossh_calls'), [])

    def test_short_quota_never_reaches_sbatch(self):
        config = self.config()
        config['budgets']['home'] = {'max_bytes': 10 ** 18}
        kit, dry = self.kit(config)
        record, prep = self.prepare(kit, dry)
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                          out=io.StringIO())
        self.assertIn('REFUSED_ROOM', str(caught.exception))
        self.assertEqual(self.calls('ossh_calls'), ['call'])
        self.assertEqual(self.calls('sbatch_calls'), [])
        self.assertFalse(any(row['event'] == 'submitted' for row in ledger.read_rows(self.ledger)))
        config['budgets']['home'] = {'max_bytes': 1024}
        config['return']['pool'] = os.path.join(self.base, 'no_such_pool')
        kit, dry = self.kit(config)
        record, prep = self.prepare(kit, dry)
        with self.assertRaises(launch.LaunchError):
            launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                          out=io.StringIO())
        self.assertEqual(self.calls('sbatch_calls'), [])

    def test_submit_once_and_one_job_partition_gate(self):
        kit, dry = self.kit()
        first, prep1 = self.prepare(kit, dry)
        result = launch.submit(prep1, self.go('GO %s\n' % first['token']), execute=True,
                               out=io.StringIO())
        self.assertEqual(result['job_id'], 4242)
        self.assertEqual(len(self.calls('sbatch_calls')), 2)
        self.assertIn('--test-only', self.calls('sbatch_calls')[0])
        rows = ledger.lookup(first['token'], self.ledger)
        self.assertEqual([row['event'] for row in rows], ['minted', 'submitted'])
        with self.assertRaises(launch.LaunchError):
            launch.submit(prep1, self.go('GO %s\n' % first['token']), execute=True,
                          out=io.StringIO())
        second, prep2 = self.prepare(kit, dry)
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep2, self.go('GO %s\n' % second['token']), out=io.StringIO())
        self.assertIn('queue behind', str(caught.exception))
        result = launch.submit(prep2, self.go('GO %s; queue behind %s\n' % (
            second['token'], first['job_name'])), out=io.StringIO())
        self.assertFalse(result['executed'])
        kit3, dry3 = self.kit(self.config(partition='advanced'))
        third, prep3 = self.prepare(kit3, dry3)
        self.assertFalse(launch.submit(prep3, self.go('GO %s\n' % third['token']),
                                       out=io.StringIO())['executed'])

    def test_a_live_job_seen_on_the_batch_host_blocks_sbatch(self):
        write(os.path.join(self.base, 'live'), 'a15_cot_apaaaaaaaaaaaaaaaa\n')
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                          out=io.StringIO())
        self.assertIn('REFUSED_LIVE', str(caught.exception))
        self.assertEqual(self.calls('sbatch_calls'), [])
        record, prep = self.prepare(kit, dry)
        result = launch.submit(prep, self.go('GO %s, queue behind aaaaaaaaaaaaaaaa\n' % record['token']),
                               execute=True, out=io.StringIO())
        self.assertEqual(result['job_id'], 4242)

    def test_status_and_fetch_through_a_fake_transport(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True, out=io.StringIO())
        seen = []

        def transport(argv, body):
            seen.append(body)
            return 0, ('4242|%s|COMPLETED|0:0|00:01:00\n' % record['job_name']).encode(), b''

        self.assertFalse(launch.status(prep, out=io.StringIO())['executed'])
        self.assertEqual(seen, [])
        result = launch.status(prep, execute=True, transport=transport, out=io.StringIO())
        self.assertEqual(result['state'], 'COMPLETED')
        self.assertEqual([row['event'] for row in ledger.lookup(record['token'], self.ledger)],
                         ['minted', 'submitted', 'ended'])
        archive = b'not really a tar but bytes'
        receipt = {'token': record['token'], 'state': 'complete',
                   'archive': {'name': 'result.tar.gz', 'bytes': len(archive),
                               'sha256': util.sha256_bytes(archive)}}
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode='w') as handle:
            for name, data in (('RECEIPT.json', json.dumps(receipt).encode()),
                               ('result.tar.gz', archive)):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                handle.addfile(info, io.BytesIO(data))
        got = launch.fetch(prep, os.path.join(self.base, 'fetched'), execute=True,
                           transport=lambda argv, body: (0, raw.getvalue(), b''), out=io.StringIO())
        self.assertEqual(got['state'], 'complete')


class TemplateTest(LaunchBase):
    def test_read_example_renders_the_read_kit_job(self):
        config = util.read_json(os.path.join(HERE, 'examples', 'read_step.config.json'))
        self.assertEqual(launch.validate_config(config), [])
        options = sbatch_lines(launch.render(config, '0123456789abcdef', b'x'))
        expected = {'--partition': 'general', '--gres': 'gpu:1', '--cpus-per-task': '16',
                    '--mem': '200G', '--time': '06:00:00', '--signal': 'B:USR1@300',
                    '--account': 'mt01', '--no-requeue': '', '--output': '/dev/null',
                    '--job-name': 'a15_cot_ap0123456789abcdef'}
        if os.path.isfile(READK_LAUNCHER):
            with open(READK_LAUNCHER) as handle:
                source = handle.read()
            body = source[source.index('def submit_argv'):source.index('def submit_command')]
            found = dict(re.findall(r"'(--[a-z-]+)=([^']*)'", body))
            self.assertEqual(found['--time'], '06:00:00')
            for key in ('--partition', '--gres', '--cpus-per-task', '--mem', '--signal',
                        '--account', '--output'):
                self.assertEqual(options[key], found[key], key)
        for key, value in expected.items():
            self.assertEqual(options[key], value, key)
        self.assertEqual([os.path.basename(arg) for arg in config['entry'][4:7]],
                         ['trace_runtime.py', '--script', 'orchard_job.py'])

    def test_tree_kit_equivalent_renders_the_tree_job(self):
        config = self.config(partition='preempt', gpus=8, cpus=96, mem_gb=1600,
                             time_limit_s=86400, signal_s=900, account='mt01')
        config['entry'] = ['/bin/bash', '{kit}/code/r.sh', 'c', '1']
        self.assertEqual(launch.validate_config(config), [])
        options = sbatch_lines(launch.render(config, '0123456789abcdef', b'x'))
        path = os.path.join(TREE_JOBS, 'jt8c.sh')
        if os.path.isfile(path):
            with open(path) as handle:
                old = handle.read()
            line = ' '.join(l for l in old.splitlines() if l.startswith('#SBATCH'))
            self.assertIn('-p %s' % options['--partition'], line)
            self.assertIn('--gres=%s' % options['--gres'], line)
            self.assertIn('-c %s' % options['--cpus-per-task'], line)
            self.assertIn('--mem=%s' % options['--mem'], line)
            self.assertIn('--signal=%s' % options['--signal'], line)
            self.assertIn('-t 24:00:00', line)
            self.assertIn('r.sh', old)
        self.assertEqual(options['--time'], '1-00:00:00')
        self.assertEqual(os.path.basename(config['entry'][1]), 'r.sh')


class LocalRunTest(LaunchBase):
    def run_batch(self, prep, wait_signal=None):
        env = dict(os.environ, SLURM_JOB_ID='77')
        env.pop('CUDA_VISIBLE_DEVICES', None)
        process = subprocess.Popen(['bash', os.path.join(prep, 'BATCH.sh')], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if wait_signal:
            time.sleep(wait_signal)
            process.send_signal(signal.SIGUSR1)
        self.assertEqual(process.wait(timeout=120) in (0, 1), True)

    def test_rendered_batch_script_stages_runs_and_returns(self):
        os.makedirs(os.path.join(self.base, 'nodetmp'))
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        self.run_batch(prep)
        folder = os.path.join(self.base, 'pool', record['token'])
        receipt = util.read_json(os.path.join(folder, 'RECEIPT.json'))
        self.assertEqual(receipt['state'], 'complete')
        self.assertIn('out/r.txt', [row['path'] for row in receipt['members']])
        self.assertEqual(receipt['kit_pins_sha256'], record['kit_pins_sha256'])
        self.assertEqual(receipt['config_sha256'], record['config_sha256'])
        self.assertTrue(os.path.isdir(os.path.join(self.base, 'nodetmp', 'a_77_' + record['token'])))

    def test_signal_before_the_limit_interrupts_and_still_returns(self):
        os.makedirs(os.path.join(self.base, 'nodetmp'))
        kit, dry = self.kit(entry='import time\ntime.sleep(60)\n')
        record, prep = self.prepare(kit, dry)
        started = time.time()
        self.run_batch(prep, wait_signal=3)
        self.assertLess(time.time() - started, 50)
        receipt = util.read_json(os.path.join(self.base, 'pool', record['token'], 'RECEIPT.json'))
        self.assertEqual(receipt['state'], 'interrupted')
        self.assertTrue(receipt['returned'])


class ReviewFindingsTest(LaunchBase):
    """Regressions for the review findings OC-02 and OC-04 to OC-08."""

    def test_oc02_config_names_and_env_are_checked(self):
        for change in ('root', 'env', 'pool'):
            config = self.config()
            config['return']['pool'] = '/project/x/pool'
            config['job']['root_parent'] = '/tmp'
            if change == 'root':
                config['job']['root_parent'] = '/tmp/split'
            elif change == 'env':
                config['return']['gcs_env'] = {'SPLIT_MODEL': '/project/u/a'}
            else:
                config['return']['pool'] = '/project/u/split/logs'
            kit, dry = self.kit(config)
            with self.assertRaises(launch.LaunchError, msg=change) as caught:
                self.prepare(kit, dry, rules=anon.load_rules(anon.WORDS))
            self.assertIn('opacity', str(caught.exception))

    def test_oc04_token_with_newline_is_refused(self):
        with self.assertRaises(launch.LaunchError):
            launch.mint_job_name('0123456789abcdef\n')

    def test_oc05_failed_squeue_fails_closed(self):
        script = ('set -euo pipefail\nsqueue(){ return 1; }\n' + launch.live_check('general') +
                  '\necho WOULD_SUBMIT\n')
        process = subprocess.Popen(['bash', '-s'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out, _ = process.communicate(script.encode())
        self.assertEqual(process.returncode, 6)
        self.assertNotIn(b'WOULD_SUBMIT', out)
        self.assertTrue(out.startswith(b'LIVE '))

    def test_oc06_room_check_reserves_the_whole_budget(self):
        need, remaining = 100 << 20, 16 << 20
        script = launch.submit_script({'job': {'partition': 'general'},
                                       'budgets': {'home': {'max_bytes': need}}},
                                      '0123456789abcdef', '#!/bin/bash\n')
        check = script.split("CHECK_0123456789abcdef'\n", 1)[1].split('\nCHECK_0123456789abcdef', 1)[0]
        home = os.path.join(self.base, 'home')
        asked = []
        real = os.posix_fallocate

        def fallocate(fd, offset, length):
            asked.append(length)
            if length > remaining:
                raise OSError(122, 'Disk quota exceeded')
            return real(fd, offset, length)

        saved = os.environ.get('HOME')
        os.environ['HOME'] = home
        os.posix_fallocate = fallocate
        try:
            with self.assertRaises(SystemExit) as caught:
                exec(check, {})
        finally:
            os.posix_fallocate = real
            os.environ['HOME'] = saved
        self.assertEqual(caught.exception.code, 3)
        self.assertEqual(asked, [need])
        self.assertEqual(os.path.getsize(os.path.join(home, '.p_probe')), 0)

    def test_oc07_a_second_claim_of_the_intent_is_refused(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        intent = os.path.join(prep, 'SUBMIT_INTENT.json')
        real_open = os.open
        calls = []

        def racing_open(path, flags, mode=0o777):
            if path == intent and not os.path.exists(intent):
                with open(intent, 'w') as handle:
                    handle.write('{"other": true}\n')
            return real_open(path, flags, mode)

        launch.os.open = racing_open
        try:
            with self.assertRaises(launch.LaunchError) as caught:
                launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                              transport=lambda argv, body: calls.append(body), out=io.StringIO())
        finally:
            launch.os.open = real_open
        self.assertIn('holds the intent', str(caught.exception))
        self.assertEqual(calls, [])

    def test_oc08_bytes_sent_are_the_bytes_checked(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        real = launch._load_prep
        calls = []

        def load_then_swap(path):
            value = real(path)
            write(os.path.join(path, 'SUBMIT.sh'), '#!/bin/bash\necho swapped\n')
            return value

        launch._load_prep = load_then_swap
        try:
            with self.assertRaises(launch.LaunchError) as caught:
                launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                              transport=lambda argv, body: calls.append(body), out=io.StringIO())
        finally:
            launch._load_prep = real
        self.assertIn('differs from its rebuild', str(caught.exception))
        self.assertEqual(calls, [])

    def test_oc11_a_kit_changed_after_it_is_read_cannot_ship(self):
        kit, dry = self.kit()
        source = os.path.join(kit, 'code', 'entry.py')
        with open(source, 'rb') as handle:
            original = handle.read()

        def provenance_then_swap(checkout, config_path):
            write(source, "MODEL = 'qwen'\n")
            return fake_provenance(checkout, config_path)

        record, prep = self.prepare(kit, dry, provenance_fn=provenance_then_swap)
        with open(os.path.join(prep, 'BATCH.sh')) as handle:
            script = handle.read()
        digits = script.split("PAYLOAD = '''\n", 1)[1].split("\n'''", 1)[0].replace('\n', '')
        with tarfile.open(fileobj=io.BytesIO(bytes.fromhex(digits)), mode='r:gz') as archive:
            shipped = archive.extractfile('kit/code/entry.py').read()
        self.assertEqual(shipped, original)
        with open(os.path.join(prep, 'kit', 'code', 'entry.py'), 'rb') as handle:
            self.assertEqual(handle.read(), original)

    def test_oc12_submit_metadata_must_match_the_scripts(self):
        kit, dry = self.kit()
        first, prep1 = self.prepare(kit, dry)
        second, _ = self.prepare(kit, dry)
        record = util.read_json(os.path.join(prep1, 'SUBMIT.json'))
        record.update(token=second['token'], job_name=second['job_name'])
        util.write_json(os.path.join(prep1, 'SUBMIT.json'), record)
        calls = []
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep1, self.go('GO %s\n' % second['token']), execute=True,
                          transport=lambda argv, body: calls.append(body), out=io.StringIO())
        self.assertIn('do not belong', str(caught.exception))
        self.assertEqual(calls, [])

    def test_oc16_altered_submission_script_or_argv_is_refused(self):
        kit, dry = self.kit()
        for change in ('script', 'argv'):
            record, prep = self.prepare(kit, dry)
            stored = util.read_json(os.path.join(prep, 'SUBMIT.json'))
            if change == 'script':
                path = os.path.join(prep, 'SUBMIT.sh')
                with open(path, 'ab') as handle:
                    handle.write(b"sbatch --wrap='echo extra'\n")
                stored['submit_sha256'] = util.sha256_file(path)[0]
            else:
                stored['argv'][-1] = "bash -s; echo extra"
            util.write_json(os.path.join(prep, 'SUBMIT.json'), stored)
            calls = []
            with self.assertRaises(launch.LaunchError, msg=change) as caught:
                launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                              transport=lambda argv, body: calls.append(body), out=io.StringIO())
            self.assertRegex(str(caught.exception), 'differs from its rebuild|transport command differs')
            self.assertEqual(calls, [])

    def test_oc17_duplicate_config_keys_are_names_too(self):
        config = self.config()
        config['return']['pool'] = '/project/x/pool'
        config['job']['root_parent'] = '/tmp'
        kit, dry = self.kit(config)
        path = os.path.join(kit, 'CONFIG.json')
        with open(path, 'rb') as handle:
            raw = handle.read()
        hidden = raw.replace(b'"job":', b'"job":{"root_parent":"/tmp/split"},"job":', 1)
        hits = anon.scan_tree(self.write_kit_copy(kit, hidden), anon.load_rules(anon.WORDS))
        self.assertTrue(any(hit['where'] == 'CONFIG.json' for hit in hits))

    def write_kit_copy(self, kit, config_raw):
        self.count += 1
        target = os.path.join(self.base, 'copy%d' % self.count)
        launch.snapshot(kit, target)
        os.chmod(os.path.join(target, 'CONFIG.json'), 0o600)
        write(os.path.join(target, 'CONFIG.json'), config_raw)
        return target

    def test_go_line_must_start_with_go(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        for text in ('NO_GO %s\n', 'NO-GO %s\n', 'GO_AFTER_FIXES %s\n', 'verdict: NO GO for %s\n'):
            with self.assertRaises(launch.LaunchError, msg=text):
                launch.submit(prep, self.go(text % record['token']), out=io.StringIO())
        self.assertFalse(launch.submit(prep, self.go('# review\nGO: %s\n' % record['job_name']),
                                       out=io.StringIO())['executed'])

    def test_oc20_a_kit_changed_during_submit_cannot_ship(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        real = launch.check_kit
        sent = []

        def check_then_swap(path, config_raw, rules):
            value = real(path, config_raw, rules)
            write(os.path.join(prep, 'kit', 'code', 'entry.py'), "MODEL = 'changed'\n")
            job = util.read_json(os.path.join(prep, 'JOB.json'))
            script, remote, _ = launch.build_submission(os.path.join(prep, 'kit'), value[0], job, rules)
            write(os.path.join(prep, 'BATCH.sh'), script)
            write(os.path.join(prep, 'SUBMIT.sh'), remote)
            return value

        launch.check_kit = check_then_swap
        try:
            with self.assertRaises(launch.LaunchError):
                launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                              transport=lambda argv, body: sent.append(body) or (0, b'JOBID=9\n', b''),
                              out=io.StringIO())
        finally:
            launch.check_kit = real
        self.assertEqual(sent, [])

    def test_oc21_two_copies_of_one_preparation_submit_once(self):
        kit, dry = self.kit(self.config(partition='advanced'))
        record, prep = self.prepare(kit, dry)
        copy = prep + '_copy'
        launch.snapshot(prep, copy)
        sent = []
        go = self.go('GO %s\n' % record['token'])

        def transport(argv, body):
            sent.append(body)
            if len(sent) == 1:
                with self.assertRaises(launch.LaunchError) as caught:
                    launch.submit(copy, go, execute=True, out=io.StringIO(), transport=transport)
                self.assertRegex(str(caught.exception), 'already claimed|in progress')
            return 0, ('JOBID=%d\n' % (40 + len(sent))).encode(), b''

        launch.submit(prep, go, execute=True, out=io.StringIO(), transport=transport)
        self.assertEqual(len(sent), 1)
        rows = [row for row in ledger.lookup(record['token'], self.ledger) if row['event'] == 'submitted']
        self.assertEqual(len(rows), 1)
        with self.assertRaises(launch.LaunchError) as caught:
            launch.claim_token(record['token'])
        self.assertIn('already claimed', str(caught.exception))

    def test_concurrent_submissions_to_a_one_job_partition_are_serialized(self):
        kit, dry = self.kit()
        first, prep1 = self.prepare(kit, dry)
        second, prep2 = self.prepare(kit, dry)
        sent = []

        def transport(argv, body):
            sent.append(body)
            if len(sent) == 1:
                with self.assertRaises(launch.LaunchError) as caught:
                    launch.submit(prep2, self.go('GO %s\n' % second['token']), execute=True,
                                  out=io.StringIO(), transport=transport)
                self.assertIn('in progress', str(caught.exception))
            return 0, b'JOBID=51\n', b''

        launch.submit(prep1, self.go('GO %s\n' % first['token']), execute=True, out=io.StringIO(),
                      transport=transport)
        self.assertEqual(len(sent), 1)
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep2, self.go('GO %s\n' % second['token']), execute=True,
                          out=io.StringIO(), transport=transport)
        self.assertIn('queue behind', str(caught.exception))

    def test_oc22_partition_comes_from_the_anchored_config(self):
        kit, dry = self.kit()
        record, prep = self.prepare(kit, dry)
        stored = util.read_json(os.path.join(prep, 'SUBMIT.json'))
        stored['partition'] = 'advanced'
        util.write_json(os.path.join(prep, 'SUBMIT.json'), stored)
        calls = []
        with self.assertRaises(launch.LaunchError) as caught:
            launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                          transport=lambda argv, body: calls.append(body), out=io.StringIO())
        self.assertIn('partition', str(caught.exception))
        self.assertEqual(calls, [])

    def test_oc26_job_file_and_every_kit_file_are_anchored(self):
        kit, dry = self.kit()
        for change in ('JOB', 'DRYRUN'):
            record, prep = self.prepare(kit, dry)
            job = util.read_json(os.path.join(prep, 'JOB.json'))
            if change == 'JOB':
                job['sessions'] = {'result.tar.gz': 'https://example.invalid/other'}
                util.write_json(os.path.join(prep, 'JOB.json'), job)
            else:
                write(os.path.join(prep, 'kit', 'DRYRUN_REPORT.json'), '{"note": "added later"}')
            config = util.read_json(os.path.join(prep, 'kit', 'CONFIG.json'))
            script, remote, _ = launch.build_submission(os.path.join(prep, 'kit'), config, job, self.loose)
            write(os.path.join(prep, 'BATCH.sh'), script)
            write(os.path.join(prep, 'SUBMIT.sh'), remote)
            stored = util.read_json(os.path.join(prep, 'SUBMIT.json'))
            stored.update(script_sha256=util.sha256_bytes(script.encode()),
                          submit_sha256=util.sha256_bytes(remote.encode()))
            util.write_json(os.path.join(prep, 'SUBMIT.json'), stored)
            calls = []
            with self.assertRaises(launch.LaunchError, msg=change) as caught:
                launch.submit(prep, self.go('GO %s\n' % record['token']), execute=True,
                              transport=lambda argv, body: calls.append(body), out=io.StringIO())
            self.assertIn('payload', str(caught.exception))
            self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
