import sys,json,importlib.util
from pathlib import Path
control,tree=sys.argv[1:3]
value=json.loads(Path(control).read_bytes())
sys.path[:]=[tree]+value['environment']['paths']
from student_pilot import carrier_c1_run as run
from unittest.mock import patch
source=Path(__file__).with_name('pc_fixture_worker.py').read_text()
classes=source[source.index('class Tokenizer:'):source.index('cfg=json.loads')]
exec(classes)
helper=Path(__file__).resolve().parents[2]/'out/rcj/pc.py'
spec=importlib.util.spec_from_file_location('pc_under_test',helper);pc=importlib.util.module_from_spec(spec);spec.loader.exec_module(pc)
with patch.object(run,'processor_for',return_value=Processor()),patch.object(run.rehearsal,'fixture_manifest',return_value={}):
 pc.worker(control,tree)
