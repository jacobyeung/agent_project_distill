"""Record bounded, read-only H1 source evidence and candidate pin checks."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {
        '../h1/FIX8.md': [(5, 7)],
        '../h1/FIX8b.md': [(3, 7)],
        '../h1/FIX8c.md': [(8, 11)],
        '../h1/ids.json': [(1, 1)],
        '../h1/payload/ids.json': [(1, 1)],
        '../h1/payload/z.sh': [(13, 15)],
        '../h1/runtime/jb.sh': [(18, 19), (46, 47)],
        '../h1/payload/jb.sh': [(18, 19), (46, 47)],
        '../h1/EXPORT_OBJECTS.txt': [(9, 16), (33, 44)],
        '../h1/build/fx/b/c.sh': [(9, 23), (404, 430)],
        '../h1/build/fx/b/gcsput.py': [(17, 18)],
        '../h1/build/fx_r7/b/c.sh': [(404, 430)],
        '../h1/build/fx_r7/b/gcsput.py': [(17, 18)],
        '../h1/build/fx/k/d12ae795.json': [(1, 1)],
        '../h1/payload/d.py': [(41, 42), (130, 135)],
        '../h1/source/code/tree/docs/carrier_c1_memory_layout.md': [(30, 51)],
        '../h1orch/L3b_submit.sh': [(1, 2), (9, 14)],
    }
    excerpts = []
    for name, ranges in sources.items():
        p = ROOT/name
        lines = p.read_text().splitlines()
        excerpts.append(dict(path=name, sha256=sha(p), excerpts=[dict(
            first=a, last=b, lines=[f'{i}: {lines[i-1]}' for i in range(a, b+1)]) for a, b in ranges]))
    (ROOT/'evidence/EXPORT_SOURCES.json').write_text(json.dumps(excerpts, indent=2)+'\n')
    source = ROOT/'../h1/payload/d.py'
    tree = ast.parse(source.read_text())
    namespace = dict(json=json, hashlib=hashlib)
    for name in ('enc', 'digest', 'identity'):
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
    config_path = ROOT/'../h1/build/fx/k/d12ae795.json'
    cfg = json.loads(config_path.read_text())
    identity = namespace['identity'](cfg)
    assert identity == 'eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8'
    assert cfg['frame_layout'] == 'duplicate'
    fx = ROOT/'../h1/build/fx/b'
    r7 = ROOT/'../h1/build/fx_r7/b'
    assert (fx/'c.sh').read_text().split('tk_persist_exports() {', 1)[1] == (r7/'c.sh').read_text().split('tk_persist_exports() {', 1)[1]
    assert (fx/'gcsput.py').read_bytes() == (r7/'gcsput.py').read_bytes()
    assert (ROOT/'../h1/runtime/jb.sh').read_bytes() == (ROOT/'../h1/payload/jb.sh').read_bytes()
    old = json.loads((ROOT/'evidence/FIX2_BEFORE_PINS.json').read_text())
    changed = [name for name, digest in old.items() if name.startswith('kit/') and sha(ROOT/name) != digest]
    assert changed == ['kit/launcher/binding.py'], changed
    binding = (ROOT/'kit/launcher/binding.py').read_bytes()
    assert hashlib.sha256(binding.replace(b"'17c4ffa4':'x_3fdda0fb'", b"'17c4ffa4':'x_4b3114cf'")).hexdigest() == old['kit/launcher/binding.py']
    pin_terms = ('2f7f4667', '6e4f2846e45377f5b25da0113bf70d625d41d0bee80ae26840d2dee839f85965', '1dd078da')
    hits = [name for name in old if name.startswith('kit/') and any(term.encode() in (ROOT/name).read_bytes() for term in pin_terms)]
    assert not hits, hits
    result = dict(status='PASS', changed_kit_files=changed, exact_kit_change_is_h1_deployment_only=True, training_config_pins_in_kit=hits,
        production_config=dict(key='1dd078da', sha256='9385cc71bad6424f04f50d536462e59e9fefc84b6a06767fdbef3912728a5130',
            identity=identity, source='User-supplied production key/file hash; file bytes not available locally'),
        local_config=dict(path='../h1/build/fx/k/d12ae795.json', sha256=sha(config_path),
            computed_identity=identity, frame_layout=cfg['frame_layout'],
            identity_covers_frame_layout=True, anchors=32, processor_frames=64),
        production_copy_search='No 1dd078da.json found in the accessible ../h1 tree; FIX2_SEARCH_ERRORS.log records the unreadable fixture directory.',
        exporter_matches_fx_r7=True, payload_matches_runtime_wrapper=True,
        path_rules=dict(run='SAME', namespace='SAME', deployment='CHANGED', m100='SAME', m200='SAME',
            stop_objects='SAME', done_naming_format='SAME (relative naming; deployment root CHANGED)',
            stop_claim='SAME', stop_generations='SAME', part_suffix='SAME'))
    (ROOT/'evidence/FIX2_AUDIT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
