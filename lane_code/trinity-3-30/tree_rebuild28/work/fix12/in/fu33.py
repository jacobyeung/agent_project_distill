"""fix12: synthetic unit tests of the merged kit's b/pf.py frames() with the kit tree's own resolve_read and
relocated (no frame root map set: resolve_read returns the pin path). Usage: fu33.py <kit>."""
import sys, json, os, sqlite3, hashlib
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); NEW = Path(sys.argv[1]); F = NEW.parent
for k in [k for k in os.environ if 'FRAME_ROOT_MAP' in k]: del os.environ[k]
sys.path[:0] = [str(W/'w30f1/tree'), str(NEW/'b')]
import pf
# frames() may end with census(cfg) (classify-100 preflight, fix13); it needs the real config, so it is stubbed
# here and tested by its own unit test. Recorded in the output.
STUBBED = hasattr(pf, 'census')
if STUBBED: pf.census = lambda cfg, limit=100: {}
from student_pilot.r1_persisted import scope
D = F/'futmp'
D.mkdir(); R1 = D/'root1'; R2 = D/'root2'; OUTSIDE = D/'elsewhere'
for d in (R1, R2, OUTSIDE): d.mkdir()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(name, v):
    p = D/name; p.write_text(json.dumps(v, sort_keys=True)); return dict(path=str(p), sha256=sha(p))
def db(name, rows):
    p = D/name; c = sqlite3.connect(str(p)); c.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT)')
    c.executemany('INSERT INTO rows VALUES (?,?)', [(i, json.dumps(r)) for i, r in enumerate(rows)]); c.commit(); c.close()
    return dict(path=str(p), sha256=sha(p))
def frame(d, rel):
    p = d/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'png' + rel.encode()); return str(p)
def row(*paths): return dict(student_input=dict(frames=[dict(path=x) for x in paths]))
fa = frame(R1, 'k6tk/a.png'); fb = frame(R2, 'u/b.png'); fo = frame(OUTSIDE, 'k6tk/o.png'); fp = frame(R1, 'k7pd/p.png')
link = R1/'k6tk/link.png'; link.symlink_to(fo)
def receipt(name, dbpin): return obj(name + '.json', dict(schema='c1-stream-v1', stream=name, database=dbpin))
good = dict(pointing=receipt('pointing', db('p.sqlite', [dict(x=1), row(fa)])),
            vqa=receipt('vqa', db('v.sqlite', [row(fb)])),
            mdg=dict(path=str(D/'absent_mdg.json'), sha256='0'*64))
# pose mix: source 0 has prefix k7pd; its first frame row (outside the roots) does not carry the prefix
pose_db = db('pose.sqlite', [row(fo), row(fp)])
good['pose'] = obj('mix.json', dict(schema='c1-pose-mix-v1', sources=[dict(kind='rows', receipt=receipt('pose0', pose_db), frame_prefix=str(R1/'k7pd')),
                                                                      dict(kind='rows', receipt=receipt('pose1', db('pose1.sqlite', [row(fa)])))]))
roots = [str(R1), str(R2)]
def run(streams, rts):
    try:
        with scope({}):
            return 'PASS ' + json.dumps(pf.frames(dict(streams=streams), rts), sort_keys=True)
    except ValueError as e:
        return 'REFUSE ' + str(e)
res = {}
res['U1_all_sources_under_roots (expect PASS, pose/0 sample honours frame_prefix)'] = run(good, roots)
res['U2_pointing_frame_outside_roots (expect R1_FRAME_ROOT_REFUSED:pointing)'] = run(dict(good, pointing=receipt('pointing2', db('p2.sqlite', [row(fo)]))), roots)
res['U3a_no_roots (expect R1_FRAME_ROOT_MISSING)'] = run(good, [])
res['U3b_root_absent (expect R1_FRAME_ROOT_MISSING)'] = run(good, [str(R1), str(D/'nope')])
res['U4_database_absent (expect R1_FRAME_PREFLIGHT_DATABASE_MISSING:vqa)'] = run(dict(good, vqa=receipt('vqa4', dict(path=str(D/'none.sqlite'), sha256='1'*64))), roots)
res['U5_no_frame_rows (expect R1_FRAME_PIN_MISSING:vqa)'] = run(dict(good, vqa=receipt('vqa5', db('v5.sqlite', [dict(a=1), dict(student_input=dict(frames=[]))]))), roots)
res['U6_frame_file_missing_under_root (expect R1_FRAME_ROOT_REFUSED:vqa)'] = run(dict(good, vqa=receipt('vqa6', db('v6.sqlite', [row(str(R2/'u/missing.png'))]))), roots)
res['U7_symlink_under_root_to_outside (expect R1_FRAME_ROOT_REFUSED:vqa)'] = run(dict(good, vqa=receipt('vqa7', db('v7.sqlite', [row(str(link))]))), roots)
res['U8_prefix_with_no_matching_row (expect R1_FRAME_PIN_MISSING:pose/0)'] = run(dict(good, pose=obj('mix8.json', dict(schema='c1-pose-mix-v1', sources=[dict(kind='rows', receipt=receipt('pose8', pose_db), frame_prefix=str(D/'zz'))]))), roots)
expect = ['PASS', 'R1_FRAME_ROOT_REFUSED:pointing:', 'R1_FRAME_ROOT_MISSING', 'R1_FRAME_ROOT_MISSING', 'R1_FRAME_PREFLIGHT_DATABASE_MISSING:vqa',
          'R1_FRAME_PIN_MISSING:vqa', 'R1_FRAME_ROOT_REFUSED:vqa:', 'R1_FRAME_ROOT_REFUSED:vqa:', 'R1_FRAME_PIN_MISSING:pose/0']
ok = [(e == 'PASS' and v.startswith('PASS')) or (e != 'PASS' and v.startswith('REFUSE ' + e)) for e, v in zip(expect, res.values())]
res['census_stubbed'] = STUBBED; res['all_as_expected'] = all(ok); res['per_case_ok'] = ok
(F/'TEST_FRAMES_33.json').write_text(json.dumps(res, indent=1) + '\n'); print(json.dumps(res, indent=1))
