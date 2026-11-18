"""Run all discovered tests under the same bounded, offline policy."""
import hashlib
import importlib.util
import importlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import time
import traceback
import types
import unittest
from urllib.parse import urlsplit,parse_qs,unquote

L = Path(__file__).resolve().parents[2]
tree = Path(os.environ.get('R2_TREE', L/'work/tree_r1')).resolve()
lane = Path(os.environ.get('R2_LANE_ROOT', L)).resolve()
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(tree), str(tree/'generator/derivgen_v7'), str(tree/'generator/ground_rows_out')]
sys.path.insert(0,str(Path(__file__).parent))
from compact_tmp import compact, inventory
import compact_tmp
temp_root = lane/'work/tmp'
temp_root.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(temp_root)
package_files=None
if os.environ.get('R2_PACKAGE_MEMBERS'):
    manifest=Path(os.environ['R2_PACKAGE_MEMBERS'])
    package_files={manifest.parent/name for name in json.loads(manifest.read_text())}
    package_files.add(manifest)
os.environ.update(TMPDIR=str(temp_root), R2_PROOFS=str(output), R2_FIXTURES=str(L/'fixtures'),
                  HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HOME=str(temp_root/'hf'),
                  XDG_CACHE_HOME=str(temp_root/'cache'),XDG_CONFIG_HOME=str(temp_root/'config'),
                  MPLCONFIGDIR=str(temp_root/'mpl'),TRITON_CACHE_DIR=str(temp_root/'triton'),
                  TORCH_HOME=str(temp_root/'torch'),CONDA_PKGS_DIRS=str(temp_root/'conda'))
for key in ('STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT','LANE_TEST_OUTPUT',
            'B2_TEST_OUTPUT','B9_TEST_OUTPUT','B11_TEST_OUTPUT'):
    os.environ[key] = str(temp_root/key.lower())
    Path(os.environ[key]).mkdir(parents=True,exist_ok=True)
os.environ['CLEAN_VSI590K_WORKSPACE'] = str(tree)

def size(root):
    return sum(inventory(root).values())

class RetainedDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(temp_root))
    def __enter__(self): return self.name
    def __exit__(self, *args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory = RetainedDirectory
hits = {}
def code_digest(code):
    def constant(value):
        if isinstance(value,types.CodeType):return ('code',code_digest(value))
        if isinstance(value,tuple):return ('tuple',tuple(constant(v) for v in value))
        if isinstance(value,frozenset):return ('frozenset',tuple(sorted(repr(constant(v)) for v in value)))
        return (type(value).__name__,repr(value))
    value=(code.co_argcount,code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,
           code.co_code.hex(),tuple(constant(v) for v in code.co_consts),code.co_names,
           code.co_varnames,code.co_freevars,code.co_cellvars,code.co_firstlineno,
           code.co_qualname,code.co_linetable.hex(),code.co_exceptiontable.hex())
    return hashlib.sha256(repr(value).encode()).hexdigest()
snapshots={};expected_codes={};rejected_codes={}
source_python=[p for p in tree.rglob('*.py')
               if not set(p.relative_to(tree).parts)&{'artifacts','.git','__pycache__'}]
for p in source_python:
    raw=p.read_bytes();snapshots[str(p.relative_to(tree))]=hashlib.sha256(raw).hexdigest()
    try:pending=[compile(raw,str(p),'exec',dont_inherit=True)]
    except SyntaxError:continue
    expected_codes[str(p)]=set()
    while pending:
        code=pending.pop();expected_codes[str(p)].add(code_digest(code))
        pending.extend(v for v in code.co_consts if isinstance(v,types.CodeType))
mon = sys.monitoring
mon.use_tool_id(4, 'build-proof')
def started(code, offset):
    if code.co_filename.startswith(str(tree)+'/'):
        if code_digest(code) in expected_codes.get(code.co_filename,()):
            mon.set_local_events(4, code, mon.events.LINE)
        else:rejected_codes[code.co_filename]=rejected_codes.get(code.co_filename,0)+1
    return mon.DISABLE
def line(code, number):
    hits.setdefault(code.co_filename, set()).add(number)
    return mon.DISABLE
mon.register_callback(4, mon.events.PY_START, started)
mon.register_callback(4, mon.events.LINE, line)
denied = []
reserve_probe=False
def writable(path):
    p=Path(os.fsdecode(path)).resolve()
    if not any(p==root or root in p.parents for root in (temp_root,output)):
        raise PermissionError('Build file policy refuses '+str(p))
def audit(event, args):
    if (event == 'subprocess.Popen' and compact_tmp.inventory_root
            and (compact_tmp.inventory_root == str(temp_root) or compact_tmp.inventory_root.startswith(str(temp_root)+'/'))
            and args[1] == ['/usr/bin/find', compact_tmp.inventory_root, '-type', 'f', '-printf', r'%s\t%p\0']):
        return
    if reserve_probe and event=='subprocess.Popen' and args[1]==['df','-BG','--output=avail','/scratch']:
        return
    if event in ('os.'+'remove','os.'+'rmdir','shutil.'+'rmtree','os.system','socket.connect','socket.bind','os.fork','os.posix_spawn','subprocess.Popen'):
        denied.append(dict(event=event, path=str(args[0])[:250] if args else ''))
        raise PermissionError('Build policy refuses '+event)
    if event in ('os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes)):
        raw_path=os.path.abspath(os.fsdecode(args[0]))
        if raw_path=='/home' or raw_path.startswith(('/home/','/data')):
            raise PermissionError('Build policy refuses external shared-directory scans')
        # The trusted inventory walker starts at one resolved local root and
        # traverses only directory entries that are explicitly not symlinks.
        # Avoid resolving every ancestor again for every per-test census.
        census=compact_tmp.inventory_root
        if census and (census==str(temp_root) or census.startswith(str(temp_root)+'/')):
            raw=os.fsdecode(args[0])
            if raw==census or raw.startswith(census+'/'):return
        path=Path(os.fsdecode(args[0])).resolve()
        if str(path).startswith(('/home/','/data')) or path==Path('/home'):
            raise PermissionError('Build policy refuses external shared-directory scans')
    if event=='sqlite3.connect':
        value=str(args[0]);readonly=False
        if value.startswith('file:'):
            uri=urlsplit(value);query=parse_qs(uri.query)
            if query.get('mode')==['memory']:return
            value=unquote(uri.path);readonly=query.get('mode')==['ro']
        if value!=':memory:':
            p=Path(value).resolve()
            if not readonly:writable(p)
            elif p!=lane and lane not in p.parents:
                raise PermissionError('Build file policy refuses '+str(p))
    if event in ('os.mkdir','os.chmod','os.utime','os.rename','os.link','os.symlink'):
        paths=args[:2] if event in ('os.rename','os.link') else args[1:2] if event=='os.symlink' else args[:1]
        for path in paths:
            if isinstance(path,(str,bytes)):
                try:writable(path)
                except PermissionError:
                    denied.append(dict(event=event,path=os.fsdecode(path),writing=True))
                    raise
    if event == 'open' and isinstance(args[0], (str, bytes)):
        raw_path=os.path.abspath(os.fsdecode(args[0]))
        if raw_path=='/home' or raw_path.startswith(('/home/','/data')):
            raise PermissionError('Build file policy refuses '+raw_path)
        p = Path(os.fsdecode(args[0])).resolve()
        flags = args[2]
        writing = bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT))
        if writing and p!=Path('/dev/null'):writable(p)
        inside = p == lane or lane in p.parents
        if writing and (p == lane/'work/base' or lane/'work/base' in p.parents):
            raise PermissionError('Untouched base is read-only')
        library = any(p == q or q in p.parents for q in (Path(sys.prefix),Path(sys.base_prefix),Path('/usr'),Path('/etc'),Path('/proc'),Path('/sys'),Path('/dev')))
        if writing and not inside and p != Path('/dev/null') or not writing and not inside and not library:
            denied.append(dict(event=event, path=str(p), writing=writing))
            raise PermissionError('Build file policy refuses '+str(p))
sys.addaudithook(audit)
import multiprocessing.process
def no_child(*args, **kwargs): raise PermissionError('Build policy refuses child processes')
multiprocessing.process.BaseProcess.start = no_child

records = []
def restore_imports(state,path):
    sys.path[:]=path
    for name,module in list(sys.modules.items()):
        if name not in state:
            source=vars(module).get('__file__') if isinstance(module,types.ModuleType) else None
            if isinstance(source,str) and source.startswith(str(temp_root)+'/') and not source.startswith(str(tree)+'/'):
                sys.modules.pop(name,None)
                parent,_,child=name.rpartition('.')
                container=sys.modules.get(parent)
                if isinstance(container,types.ModuleType) and vars(container).get(child) is module:
                    vars(container).pop(child,None)
    for name,module in state.items():
        if sys.modules.get(name) is not module:
            sys.modules[name]=module
            parent,_,child=name.rpartition('.')
            container=sys.modules.get(parent)
            if isinstance(container,types.ModuleType):setattr(container,child,module)

class Result(unittest.TextTestResult):
    def addError(self, test, error):
        super().addError(test,error)
        (output/'latest_error.json').write_text(json.dumps(dict(test=test.id(),traceback=self._exc_info_to_string(error,test))))
        (output/'live_errors.json').write_text(json.dumps([(t.id(), e) for t,e in self.errors],indent=2))
    def addFailure(self, test, error):
        super().addFailure(test,error)
        (output/'latest_failure.json').write_text(json.dumps(dict(test=test.id(),traceback=self._exc_info_to_string(error,test))))
        (output/'live_failures.json').write_text(json.dumps([(t.id(), e) for t,e in self.failures],indent=2))
    def startTest(self, test):
        global reserve_probe
        self.started = time.monotonic()
        self.import_state=dict(sys.modules)
        self.import_path=list(sys.path)
        reserve_probe=True
        try:
            available=subprocess.run(['df','-BG','--output=avail','/scratch'],check=True,capture_output=True,text=True)
        finally:reserve_probe=False
        self.scratch_available_gib=int(available.stdout.splitlines()[-1].strip().rstrip('G'))
        if self.scratch_available_gib < 85 or shutil.disk_usage('/scratch').free < 85*1024**3:
            raise RuntimeError('Scratch reserve is below the build limit')
        before = inventory(temp_root)
        self.before_bytes = sum(before.values())
        if self.before_bytes > 200_000_000:
            raise RuntimeError('Temporary storage cap reached')
        self.prior_files = set(before)
        super().startTest(test)
    def stopTest(self, test):
        super().stopTest(test)
        restore_imports(self.import_state,self.import_path)
        files = inventory(temp_root)
        current = sum(files.values())
        records.append(dict(test=test.id(), before_bytes=self.before_bytes, after_bytes=current,
                            scratch_available_gib=self.scratch_available_gib,
                            seconds=time.monotonic()-self.started))
        (output/'progress.json').write_text(json.dumps(dict(completed=self.testsRun,last=test.id(),tmp_bytes=current)))
        overwritten = compact(temp_root, preserved_files=self.prior_files,files=files,package_files=package_files)
        with (output/'scratch_receipts.jsonl').open('a') as f:
            for row in overwritten:f.write(json.dumps(row)+'\n')
        if current > 200_000_000:
            try:raise RuntimeError('Test exceeded the bounded temporary storage policy')
            except RuntimeError:self.addError(test,sys.exc_info())
            passed[:]=[name for name in passed if name!=test.id()]
    def addSuccess(self,test):
        super().addSuccess(test)
        passed.append(test.id())

pattern = 'test_*.py' if os.environ.get('R2_ALL_TESTS') == '1' else 'test_r2*.py'
paths=sorted(tree.rglob(pattern)) if os.environ.get('R2_ALL_TESTS')=='1' else sorted((tree/'tests').glob(pattern))
paths=[p for p in paths if not set(p.relative_to(tree).parts)&{'artifacts','.git','__pycache__'}]
group=os.environ.get('R2_SUITE_GROUP')
if group:
    def group_of(path):
        relative=path.relative_to(tree)
        return ('r2' if path.name.startswith('test_r2') else 'legacy') if relative.parts[0]=='tests' else 'generator'
    paths=[path for path in paths if group_of(path)==group]
names = sys.argv[2:] or ['.'.join(p.relative_to(tree).with_suffix('').parts) for p in paths]
def module_name(name):
    parts=name.split('.')
    for end in range(len(parts),0,-1):
        if tree.joinpath(*parts[:end]).with_suffix('.py').is_file():return '.'.join(parts[:end])
    return None
if False and tree.name == 'tree_b01ce449' and not sys.argv[2:]:
    previous=json.loads(Path(os.environ.get('R2_BASE_RESULTS',output.parent/'suite_tree/results.json')).read_text())
    names=[]
    for test,error in previous['failures']+previous['errors']:
        match=re.search(r'(?:tests|generator)(?:\.[A-Za-z0-9_]+)+',test)
        if match:
            selected=match.group()
            if module_name(selected):names.append(selected)
    names=sorted(set(names))
suite = unittest.TestSuite()
modules = []
module_suites = {}
def add_part(name,part):
    key=module_name(name) or name
    if key not in module_suites:
        grouped=unittest.TestSuite()
        module_suites[key]=grouped
        modules.append(grouped)
        suite.addTest(grouped)
    module_suites[key].addTests(part)
passed = []
fatal = None
class ImportFailure(unittest.TestCase):
    def __init__(self, name, message):
        super().__init__('runTest')
        self.name, self.message = name, message
    def id(self): return self.name
    def __str__(self): return self.name
    def runTest(self): raise RuntimeError(self.message)
mon.set_events(4, mon.events.PY_START)
for name in names:
    try:
        module=module_name(name)
        if module:importlib.import_module(module)
        part = unittest.defaultTestLoader.loadTestsFromName(name)
        add_part(name,part)
    except BaseException as error:
        message = type(error).__name__+': '+str(error)
        part = unittest.TestSuite([ImportFailure(name,message)])
        add_part(name,part)
if tree.name != 'tree_b01ce449' and not sys.argv[2:] and group in (None,'r2') and (L/'fixtures/grammar/work/test_trace_grammar.py').exists():
    spec = importlib.util.spec_from_file_location('published_grammar_tests',L/'fixtures/grammar/work/test_trace_grammar.py')
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(L/'fixtures/grammar/work'))
    spec.loader.exec_module(module)
    if (tree/'student_pilot/trace_grammar.py').is_file():
        import student_pilot.trace_grammar
        module.grammar = student_pilot.trace_grammar
    part = unittest.defaultTestLoader.loadTestsFromModule(module)
    modules.append(part)
    suite.addTests(part)
(output/'TEST_INVENTORY.json').write_text(json.dumps(dict(modules=names,discovered_tests=suite.countTestCases()),indent=2))
for name in ('live_errors.json','live_failures.json'):
    (output/name).write_text('[]\n')
(output/'progress.json').write_text(json.dumps(dict(completed=0,last=None,status='running')))
result = Result(sys.stdout, True, 1)
completed_modules = 0
(output/'scratch_receipts.jsonl').write_text('')
try:
    with (output/'tests.log').open('w') as stream:
        result = Result(unittest.runner._WritelnDecorator(stream), True, 2)
        for part in modules:
            module_state,module_path=dict(sys.modules),list(sys.path)
            try:part.run(result)
            finally:restore_imports(module_state,module_path)
            completed_modules += 1
            overwritten = compact(temp_root,package_files=package_files)
            with (output/'scratch_receipts.jsonl').open('a') as f:
                for row in overwritten: f.write(json.dumps(row)+'\n')
except BaseException: fatal = traceback.format_exc()
finally: mon.set_events(4, 0)
record = dict(tests=result.testsRun,passed=passed,failures=[(t.id(),e) for t,e in result.failures],
              errors=[(t.id(),e) for t,e in result.errors],skips=[(t.id(),e) for t,e in result.skipped],fatal=fatal,tmp_bytes=size(temp_root),
              completed_modules=completed_modules,scheduled_modules=len(modules),complete=completed_modules==len(modules) and fatal is None)
record['coverage_code_filter']='compiled-source fingerprint'
(output/'results.json').write_text(json.dumps(record,indent=2)+'\n')
(output/'source_hashes.json').write_text(json.dumps(snapshots,indent=2)+'\n')
(output/'hits.json').write_text(json.dumps({str(Path(k).relative_to(tree)):sorted(v) for k,v in hits.items()}))
(output/'rejected_code_objects.json').write_text(json.dumps({str(Path(k).relative_to(tree)):v for k,v in rejected_codes.items()},indent=2)+'\n')
(output/'policy_refusals.json').write_text(json.dumps(denied,indent=2)+'\n')
(output/'temporary_sizes.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in record.items()}))
sys.exit(bool(fatal) or not result.wasSuccessful())
