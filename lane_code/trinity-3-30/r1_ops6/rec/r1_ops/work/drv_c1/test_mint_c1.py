"""Mocked C export absence checks; no network or capabilities."""
import importlib.util,io,sys,tempfile,urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
W=Path(__file__).resolve().parent;T=Path(tempfile.mkdtemp(prefix='mint_c1_',dir=W))
spec = importlib.util.spec_from_file_location('mint_fresh', W/'mint_fresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for label in ('absent', 'exists', 'auth_error', 'fallback_exists'):
    calls = []
    minted = []
    def install(helper):
        helper.BUCKET = 'local-test'
        helper.token = lambda: 'LOCAL_FAKE_TOKEN'
        helper.mint = lambda *a: minted.append(a)
    fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=install))
    def request(req, timeout):
        calls.append(req.full_url)
        if '/o?' in req.full_url:
            if label == 'auth_error':
                raise urllib.error.HTTPError(req.full_url, 403, 'refused', {}, None)
            return io.BytesIO(b'{"items":[{"name":"occupied"}]}' if label == 'fallback_exists' else b'{}')
        if label == 'absent':
            raise urllib.error.HTTPError(req.full_url, 404, 'absent', {}, None)
        if label == 'auth_error':
            raise urllib.error.HTTPError(req.full_url, 403, 'refused', {}, None)
        return SimpleNamespaceContext()
    class SimpleNamespaceContext:
        def __enter__(self): return self
        def __exit__(self, *args): return False
    argv = ['mint_fresh.py', str(T/(label+'.json')), '8865619b', '05b8ac69', 'm400', 'm600', 'mstop', 'mstopB', 'mstopC']
    with patch.object(sys, 'argv', argv), patch.object(module.importlib.util, 'spec_from_file_location', return_value=fake_spec), patch.object(module.importlib.util, 'module_from_spec', return_value=SimpleNamespace()), patch.object(module.urllib.request, 'urlopen', side_effect=request):
        try:
            module.main()
        except SystemExit:
            assert label != 'absent'
        else:
            assert label == 'absent'
    assert len(minted) == (1 if label == 'absent' else 0)
    assert len(calls) == (21 if label == 'absent' else 2 if label == 'exists' else 1)
    print('PASS mint export check', label)
print('No Slurm, GCS, or real session calls occurred')
