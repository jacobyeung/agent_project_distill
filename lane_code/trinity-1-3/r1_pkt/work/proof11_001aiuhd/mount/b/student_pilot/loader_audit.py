import json, os
from pathlib import Path
def main(x):
    assert x == str(Path(os.environ['FIXTURE_ROOT'])/'mount')
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    Path(os.environ['FIXTURE_ROOT'], 'loader_called.json').write_text(json.dumps({'status':'PASS','fixture':True}))
    print('loader-audit call reached under set -u', flush=True)
