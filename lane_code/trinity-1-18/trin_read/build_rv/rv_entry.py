"""Enter the unchanged kit after recording the actual engine version."""
import json
from pathlib import Path
import runpy
import sys
import vllm

if vllm.__version__ != '0.32.0':
    raise RuntimeError('ReVSI requires vLLM 0.32.0; no substitute allowed')
config = json.loads(Path(sys.argv[2]).read_text())
package = Path(config['spec']['package'])
sys.argv = [str(package/'launcher/trace_runtime.py'), '--root', sys.argv[1],
            '--config', sys.argv[2], '--script', str(package/'reader/chain.py')]
runpy.run_path(sys.argv[0], run_name='__main__')
