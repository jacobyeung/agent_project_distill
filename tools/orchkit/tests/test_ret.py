"""Tests for the job driver and return path, against a fake pool directory and a fake GCS server."""
import base64
import hashlib
import json
import os
import socketserver
import sys
import tarfile
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import pins, ret, util  # noqa: E402

QUANTUM = 256 * 1024


class FakeSessions(object):
    """In-memory GCS resumable sessions. reset_at: close the connection once after reading this
    many body bytes of a chunk; persistence is rounded down to 256 KiB as GCS does."""

    def __init__(self, reset_at=None):
        self.objects = {}
        self.reset_at = reset_at
        self.resets = 0
        self.requests = []
        self.generation = 1000


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_PUT(self):
        fake = self.server.fake
        name = self.path.split('?')[0].strip('/')
        stored = fake.objects.setdefault(name, {'data': b'', 'done': None})
        length = int(self.headers.get('Content-Length', '0'))
        crange = self.headers.get('Content-Range', '')
        fake.requests.append((name, crange, length))
        if stored['done'] is not None:
            return self.reply(200, stored['done'])
        spec, _, total = crange[len('bytes '):].partition('/')
        total = int(total)
        if spec == '*':
            self.rfile.read(length)
            if len(stored['data']) == total:
                return self.finish_object(name, stored, total)
            return self.incomplete(stored)
        start, end = (int(part) for part in spec.split('-'))
        if start != len(stored['data']):
            self.rfile.read(length)
            return self.incomplete(stored)
        if fake.reset_at is not None and fake.resets == 0 and length > fake.reset_at:
            body = self.rfile.read(fake.reset_at)
            keep = len(body) // QUANTUM * QUANTUM
            stored['data'] += body[:keep]
            fake.resets += 1
            self.close_connection = True
            self.connection.shutdown(2)
            return
        body = self.rfile.read(length)
        stored['data'] += body
        if len(stored['data']) == total:
            return self.finish_object(name, stored, total)
        return self.incomplete(stored)

    def incomplete(self, stored):
        self.send_response(308)
        if stored['data']:
            self.send_header('Range', 'bytes=0-%d' % (len(stored['data']) - 1))
        self.send_header('Content-Length', '0')
        self.end_headers()

    def finish_object(self, name, stored, total):
        fake = self.server.fake
        fake.generation += 1
        stored['done'] = {'name': name, 'size': str(total), 'generation': str(fake.generation),
                          'md5Hash': base64.b64encode(hashlib.md5(stored['data']).digest())
                          .decode('ascii')}
        return self.reply(200, stored['done'])

    def reply(self, status, value):
        data = json.dumps(value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(data)


class Server(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


def serve(fake):
    server = Server(('127.0.0.1', 0), Handler)
    server.fake = fake
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, 'http://127.0.0.1:%d' % server.server_address[1]


def write(path, data):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))


class UploadTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix='orchkit_ret_')

    def test_reset_in_mid_upload_resumes_by_range(self):
        fake = FakeSessions(reset_at=QUANTUM + 1000)
        server, url = serve(fake)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        data = os.urandom(3 * QUANTUM + 17)
        write(os.path.join(self.base, 'a.bin'), data)
        meta = ret.upload_session(url + '/obj?upload_id=1', os.path.join(self.base, 'a.bin'),
                                  chunk=2 * QUANTUM, sleep=lambda s: None)
        self.assertEqual(fake.objects['obj']['data'], data)
        self.assertEqual(fake.resets, 1)
        self.assertEqual(meta['resets'], 1)
        ranges = [row[1] for row in fake.requests]
        self.assertIn('bytes */%d' % len(data), ranges)
        self.assertIn('bytes %d-%d/%d' % (QUANTUM, 3 * QUANTUM - 1, len(data)), ranges)
        self.assertEqual(ranges[0], 'bytes 0-%d/%d' % (2 * QUANTUM - 1, len(data)))

    def test_empty_file_and_md5_mismatch(self):
        fake = FakeSessions()
        server, url = serve(fake)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        write(os.path.join(self.base, 'e.bin'), b'')
        meta = ret.upload_session(url + '/e', os.path.join(self.base, 'e.bin'))
        self.assertEqual(meta['size'], '0')
        write(os.path.join(self.base, 'f.bin'), b'abc')
        fake.objects['f'] = {'data': b'', 'done': {'size': '3', 'md5Hash': 'xx', 'generation': '1'}}
        with self.assertRaises(ret.UploadError):
            ret.upload_session(url + '/f', os.path.join(self.base, 'f.bin'))


class JobTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix='orchkit_ret_')
        self.bundle = os.path.join(self.base, 'b')
        self.kit = os.path.join(self.bundle, 'kit')
        self.root = os.path.join(self.base, 'root')
        self.pool = os.path.join(self.base, 'pool')
        os.makedirs(self.pool)
        self.uploads = []

    def make(self, entry_code, budget=10 ** 7, stage_items=(), extra_files=()):
        write(os.path.join(self.kit, 'code/entry.py'), entry_code)
        spec = [{'role': 'code', 'logical_path': 'code/entry.py'}]
        for logical, data in extra_files:
            write(os.path.join(self.kit, logical), data)
            spec.append({'role': 'input', 'logical_path': logical})
        manifest = pins.build(self.kit, {'entries': spec})
        util.write_json(os.path.join(self.kit, 'PINS.json'), manifest)
        config = {'schema': 'orchkit-config-v1', 'kit_pins_sha256': pins.kit_identity(manifest),
                  'job': {'partition': 'general', 'gpus': 0, 'cpus': 1, 'mem_gb': 1,
                          'time_limit_s': 60, 'signal_s': 30, 'nice': 0},
                  'entry': [sys.executable, '{kit}/code/entry.py', '{out}'],
                  'n_items': 1, 'budgets': {'return': {'max_bytes': budget},
                                            'pool': {'max_bytes': 10 ** 8}},
                  'records': [], 'spec': {}, 'stage': list(stage_items),
                  'return': {'pool': self.pool, 'gcs_prefix': 'gs://bucket/p'}}
        util.write_json(os.path.join(self.kit, 'CONFIG.json'), config)
        util.write_json(os.path.join(self.bundle, 'JOB.json'),
                        {'token': '0123456789abcdef', 'job_name': 'a15_cot_ap0123456789abcdef',
                         'sessions': {'result.tar.gz': 'fake://r', 'RECEIPT.json': 'fake://c'}})

    def uploader(self, uri, path):
        with open(path, 'rb') as handle:
            self.uploads.append((uri, os.path.basename(path), len(handle.read())))
        return {'generation': '77', 'size': str(os.path.getsize(path))}

    def members(self, receipt):
        archive = os.path.join(self.pool, '0123456789abcdef', 'result.tar.gz')
        with tarfile.open(archive) as handle:
            return dict((item.name, handle.extractfile(item).read()) for item in handle
                        if item.isfile())

    def test_complete_job_returns_to_both_channels(self):
        self.make("import os,sys\nopen(os.path.join(sys.argv[1],'r.json'),'w').write('{}')\n")
        receipt = ret.run_job(self.bundle, self.root, uploader=self.uploader)
        self.assertEqual(receipt['state'], 'complete')
        self.assertTrue(receipt['returned'])
        self.assertTrue(receipt['pool']['verified'])
        self.assertEqual(receipt['gcs'], {'uri': 'gs://bucket/p/0123456789abcdef/result.tar.gz',
                                          'generation': '77', 'verified': True, 'resets': 0})
        self.assertEqual(self.uploads[0][:2], ('fake://r', 'result.tar.gz'))
        self.assertEqual(self.uploads[1][:2], ('fake://c', 'RECEIPT.json'))
        self.assertIn('out/r.json', self.members(receipt))
        names = [row['path'] for row in receipt['members']]
        self.assertIn('out/r.json', names)
        pooled = util.read_json(os.path.join(self.pool, '0123456789abcdef', 'RECEIPT.json'))
        self.assertEqual(pooled['token'], '0123456789abcdef')
        self.assertEqual(pooled['config_sha256'],
                         util.sha256_file(os.path.join(self.kit, 'CONFIG.json'))[0])

    def test_entry_that_raises_still_returns_its_traceback(self):
        self.make("raise RuntimeError('boom in entry')\n")
        receipt = ret.run_job(self.bundle, self.root, uploader=self.uploader)
        self.assertEqual(receipt['state'], 'failed')
        self.assertNotEqual(receipt['rc'], 0)
        self.assertTrue(receipt['returned'])
        self.assertIn('boom in entry', receipt['error'])
        self.assertIn(b'Traceback', self.members(receipt)['logs/entry.log'])

    def test_staging_fault_still_returns_a_receipt_with_the_traceback(self):
        self.make('pass\n', stage_items=[{'logical_path': 'in/missing.bin', 'unpack': 'file',
                                          'dest': 'x', 'policy': 'new'}])
        receipt = ret.run_job(self.bundle, self.root, uploader=self.uploader)
        self.assertEqual(receipt['state'], 'staging_failed')
        self.assertTrue(receipt['returned'])
        self.assertIn(b'StageError', self.members(receipt)['logs/TRACEBACK.txt'])

    def test_return_above_budget_refuses_before_upload_and_lists_members(self):
        members = [('out/big.bin', '/nonexistent', 5000), ('out/a', '/nonexistent', 10)]
        with self.assertRaises(ret.BudgetError) as caught:
            ret.build_archive(members, os.path.join(self.base, 'never.tar.gz'), 2048)
        self.assertEqual([row['path'] for row in caught.exception.members], ['out/big.bin', 'out/a'])
        self.assertFalse(os.path.exists(os.path.join(self.base, 'never.tar.gz')))
        self.make("import os,sys\nopen(os.path.join(sys.argv[1],'big.bin'),'wb').write(os.urandom(200000))\n",
                  budget=100000)
        receipt = ret.run_job(self.bundle, self.root, uploader=self.uploader)
        self.assertEqual(receipt['state'], 'over_budget')
        self.assertEqual(receipt['refused'][0]['path'], 'out/big.bin')
        self.assertTrue(receipt['returned'])
        self.assertLess(self.uploads[0][2], 100000)
        self.assertNotIn('out/big.bin', self.members(receipt))

    def test_gpu_guard_refuses_a_gpu_job_without_devices(self):
        self.make('pass\n')
        saved = os.environ.pop('CUDA_VISIBLE_DEVICES', None)
        try:
            receipt = ret.run_job(self.bundle, self.root, expect_gpus=1, uploader=self.uploader)
        finally:
            if saved is not None:
                os.environ['CUDA_VISIBLE_DEVICES'] = saved
        self.assertEqual(receipt['state'], 'no_gpu')
        self.assertTrue(receipt['returned'])

    def test_pool_channel_failure_is_recorded_and_gcs_still_returns(self):
        self.make('pass\n')
        config = util.read_json(os.path.join(self.kit, 'CONFIG.json'))
        config['return']['pool'] = 'relative/pool'
        util.write_json(os.path.join(self.kit, 'CONFIG.json'), config)
        receipt = ret.run_job(self.bundle, self.root, uploader=self.uploader)
        self.assertFalse(receipt['pool']['verified'])
        self.assertTrue(receipt['gcs']['verified'])
        self.assertTrue(receipt['returned'])


if __name__ == '__main__':
    unittest.main()
