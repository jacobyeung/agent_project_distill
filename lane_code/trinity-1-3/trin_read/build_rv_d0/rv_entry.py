"""Enter the reviewed chain after checking engine and optional adapter identity."""
import json
from pathlib import Path
import runpy
import sys
import vllm

if vllm.__version__ != '0.32.0':
    raise RuntimeError('ReVSI requires vLLM 0.32.0; no substitute allowed')
config = json.loads(Path(sys.argv[2]).read_text())
package = Path(config['spec']['package'])
adapter = config['spec'].get('adapter_overlay')
if adapter is not None:
    import hashlib
    mounted = package/'reader/official_adapter.py'
    if (adapter['target'] != str(mounted) or
            hashlib.sha256(mounted.read_bytes()).hexdigest() != adapter['sha256']):
        raise RuntimeError('Mounted adapter overlay SHA256 differs')
sys.argv = [str(package/'launcher/trace_runtime.py'), '--root', sys.argv[1],
            '--config', sys.argv[2], '--script', str(package/'reader/chain.py')]
runpy.run_path(sys.argv[0], run_name='__main__')
