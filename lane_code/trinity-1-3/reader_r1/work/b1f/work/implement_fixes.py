from pathlib import Path
P=Path('out/src')
p=P/'b/e2e_reader/perception_memo.py';s=p.read_text().replace('from collections import OrderedDict','from collections import namedtuple').replace('DEFAULT_BYTES = 16 * 1024 ** 3\n','')
a=s.index('    bound = value.get');b=s.index('\n\ndef _process',a)
s=s[:a]+'''    ids = value['perception_memo_verify_ids'] if required else value.get('perception_memo_verify_ids', ())
    if not isinstance(ids, (list, tuple)) or any(type(i) is not str for i in ids):
        raise ValueError('invalid_perception_memo_verify_ids')
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_perception_memo_verify_ids')
    if ids and mode != 'verify':
        raise ValueError('verify_ids_require_verify_mode')
    return dict(perception_memo=mode, perception_memo_verify_ids=tuple(ids))
'''+s[b:]
a=s.index('\ndef held_bytes')
s=s[:a]+'''
HostTensor = namedtuple('HostTensor', 'value device')


def store_value(value):
    """Retain tensor payload on the host and remember its exact return device."""
    if isinstance(value, torch.Tensor):
        return HostTensor(value.detach().to(device='cpu', copy=True), value.device)
    if isinstance(value, dict):
        return {k: store_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(store_value(v) for v in value)
    return copy_value(value)


def restore_value(value):
    if isinstance(value, HostTensor):
        return value.value.to(device=value.device, copy=True)
    if isinstance(value, dict):
        return {k: restore_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(restore_value(v) for v in value)
    return copy_value(value)

'''+s[a:]
a=s.index('    def __init__(self, perception_memo');b=s.index('    def _owner',a)
s=s[:a]+'''    def __init__(self, perception_memo='on', perception_memo_verify_ids=()):
        self.pid = os.getpid()
        self.requested = perception_memo
        self.mode = perception_memo
        self.verify_ids = frozenset(perception_memo_verify_ids)
        self.item_id = None
        self.entries = {}
        self.bytes = 0
        self.events = []
        self.reads = 0
        self.start = 0
        self.hits = self.misses = 0

'''+s[b:]
s=s.replace('self.__init__(self.requested, self.limit, self.first, self.types)','self.__init__(self.requested, tuple(self.verify_ids))')
a=s.index('        self.reads = self.reads + 1');b=s.index('\n    def report',a)
s=s[:a]+'''        self.reads += 1
        self.start = len(self.events)
        self.mode = ('verify' if self.item_id in self.verify_ids else 'on') if self.requested == 'verify' else self.requested
'''+s[b:]
s=s.replace('evictions=self.evictions, events=', 'item_id=self.item_id, events=')
s=s.replace('stored, size = self.entries.pop(digest)\n            self.entries[digest] = (stored, size)\n            result = copy_value(stored)','stored, size = self.entries[digest]\n            result = restore_value(stored)')
a=s.index('        if size <= self.limit:');b=s.index('\n\ndef sam_encode',a)
s=s[:a]+'''        self.entries[digest] = (store_value(value), size)
        self.bytes += size
        return copy_value(value)
'''+s[b:];p.write_text(s)
p=P/'b/e2e_reader/real.py';s=p.read_text();s=s.replace("perception_memo_max_bytes=None, perception_memo_verify_reads=None, perception_memo_verify_types=None", "perception_memo_verify_ids=()")
s=s.replace('from .perception_memo import process_memo, DEFAULT_BYTES','from .perception_memo import process_memo')
a=s.index('                            perception_memo_max_bytes=');b=s.index('\n    socket =',a)
s=s[:a]+'''                            perception_memo_verify_ids=perception_memo_verify_ids))'''+s[b:];p.write_text(s)
p=P/'b/e2e_reader/parity.py';s=p.read_text();a=s.index('                                             perception_memo_max_bytes=');b=s.index('                                             sam3_tower=',a)
s=s[:a]+"                                             perception_memo_verify_ids=settings['perception_memo_verify_ids'],\n"+s[b:]
s=s.replace("perception_memo=settings.get('perception_memo','off')","perception_memo=settings['perception_memo']")
s=s.replace('    read_numbers = {key(t): i + 1 for i, t in enumerate(items)}\n\n','')
s=s.replace("            memo.next_read = read_numbers[key(item)]\n            memo.verify_read = memo.types is None or item['question_type'] in memo.types", "            memo.item_id = str(item['id'])")
p.write_text(s)
# Operator identity settings use the same explicit ID list.
p=P/'orchard_h10/prepare.py';s=p.read_text();a=s.index('        perception_memo_max_bytes=');b=s.index('\n',s.index("perception_memo_verify_types=",a))
s=s[:a]+"        perception_memo_verify_ids=config.get('perception_memo_verify_ids',[]))"+s[b:];p.write_text(s)
p=P/'orchard_h10/runner.py';s=p.read_text();a=s.index('                    perception_memo_max_bytes=');b=s.index('                    settings_sha256=',a)
s=s[:a]+"                    perception_memo_verify_ids=actual.get('perception_memo_verify_ids',[]),\n"+s[b:]
s=s.replace("out=Path(config['output'])/'cache'/str(index)","out=Path(config.get('cache_root',Path(config['output'])/'cache'))/str(index)")
s=s.replace("str(Path(config['output'])/'metadata/STOP')","str(config.get('stop_file',Path(config['output'])/'metadata/STOP'))")
s=s.replace("marker=out/'metadata/STOP'","marker=Path(config.get('stop_file',out/'metadata/STOP'))")
s=s.replace("    return args\n", "    if config.get('single_worker'):\n        args[args.index('--types')+1]=','.join(config['types'])\n        args[args.index('--out')+1]=str(Path(config['output'])/'metadata/journals')\n        args+=['--type-journals']\n    return args\n")
s=s.replace("for kind in (*types,*(['optional'] if optional_ready(config) else [])):","for kind in (types[:1] if config.get('single_worker') else (*types,*(['optional'] if optional_ready(config) else []))):",1)
p.write_text(s)
p=P/'h1eval/h10/launch.py';s=p.read_text().replace("'perception_memo_max_bytes','perception_memo_verify_reads','perception_memo_verify_types'","'perception_memo_verify_ids'")
a=s.index('                 perception_memo_max_bytes=');b=s.index('\n    if reviewed:',a)
s=s[:a]+"                 perception_memo_verify_ids=list((settings or {}).get('perception_memo_verify_ids',())))"+s[b:]
s=s.replace('def run(args, *, make_real=None, factory_options=None):','def run(args, *, make_real=None, factory_options=None, generators=None):')
s=s.replace('                cached_generator=None',"                cached_generator=None if generators is None else generators.get(arm)")
s=s.replace("[mapped[r['id']] for r in selected_items],perception_factory=factory,", "[mapped[r['id']] for r in (selected_items if generators is None else select_types(manifest['items'],selected(manifest['items'],args.shard),args.all_types))],perception_factory=factory,")
s=s.replace('                        generator=cached_generator','                        if generators is not None:generators[arm]=cached_generator\n                        generator=cached_generator')
s=s.replace('                if cached_generator is not None:', '                if cached_generator is not None and generators is None:')
a=s.index('\ndef parser():')
s=s[:a]+'''
def run_types(args, *, make_real=None, factory_options=None):
    """One process and one generator per arm; each type keeps its own journal."""
    from copy import copy
    from contextlib import redirect_stdout, redirect_stderr
    from orchard_h10.common import ORDER
    wanted=args.types.split(',')
    if len(set(wanted)) != len(wanted) or any(k not in ORDER for k in wanted):
        raise ValueError('Invalid type sequence')
    if args.arms != 'tower' or args.modes != 'none':
        raise ValueError('Type journals require an unperturbed tower read')
    generators={};results=[]
    try:
        for kind in wanted:
            if _REQUEST_STOP or (args.stop_file and Path(args.stop_file).exists()) or (args.stop_at is not None and time.time() >= args.stop_at):break
            part=copy(args);part.types=kind;part.all_types=args.types
            part.out=str(Path(args.out)/str(ORDER.index(kind))/str(shard(args.shard)[0]))
            root=Path(part.out);root.mkdir(parents=True,exist_ok=True)
            write_json(root/'STARTED.json',dict(type=kind,shard=args.shard))
            with (root/'STEPS.jsonl').open('a') as steps, (root/'worker.log').open('a') as log:
                commit_record(steps,dict(event='start',type=kind))
                with redirect_stdout(log), redirect_stderr(log):
                    result=run(part,make_real=make_real,factory_options=factory_options,generators=generators)
                write_json(root/'SUMMARY.json',result)
                commit_record(steps,dict(event='exit',type=kind,**result))
            results.append(dict(type=kind,**result))
            if result['completed'] != result['expected']:break
    finally:
        for generator in generators.values():
            if callable(getattr(generator,'close',None)):generator.close()
    return dict(segments=results,completed=sum(r['completed'] for r in results))

'''+s[a:]
s=s.replace("    p.add_argument('--export-cache');", "    p.add_argument('--type-journals',action='store_true')\n    p.add_argument('--export-cache');")
s=s.replace('try:print(json.dumps(run(args)));return 0','try:print(json.dumps(run_types(args) if args.type_journals else run(args)));return 0')
p.write_text(s)
p=P/'h1eval/h10/parity_adapter.py';s=p.read_text();needle="        for field in ('tree', 'frames_root', 'selector_head', 'scale_head', 'sam3', 'require_dense64'):"
s=s.replace(needle,"        for field in ('stage1_select_rule','perception_memo','perception_memo_verify_ids'):\n            if field not in receipt['inputs']['settings'] or receipt['inputs']['settings'][field] != settings[field]:\n                raise ValueError('Tower perception settings differ: ' + field)\n"+needle);p.write_text(s)
