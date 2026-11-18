import json, sys, os
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/review_h1read5/work/k')
sys.path.insert(0, str(K/'kit/launcher'))
import orchard_launcher as L, chain_save as A
W = Path(sys.argv[1]); W.mkdir()
fams = sys.argv[2].split(',')
for types, tag in ((None,'u'),('direct','d')):
    try:
        cfg = L.prepare('a00000000'+('4' if tag=='u' else '5'), W/('prep_'+tag), 544, run='469ddece', generation='mstop', families=fams, types=types)
    except Exception as e:
        print(tag, 'prepare failed', repr(e)); continue
    for withlogs in (False, True):
        src = W/f'src_{tag}_{int(withlogs)}'
        (src/'logs').mkdir(parents=True); (src/'metadata').mkdir()
        (src/'FAILED.json').write_text('{"error":"x","returncode":1}\n')
        qtypes = ['object_counting','object_abs_distance','object_size_estimation','room_size_estimation','object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','obj_appearance_order','object_rel_distance']
        for f in fams:
            for arm in ('0','budget_2048/0','budget_4096/0'):
                for fn in ('g0.jsonl','items_a0.jsonl'):
                    p = src/f/'a0/results'/arm/fn; p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(''.join(json.dumps(dict(id=f'{f}{i}',status='complete',question_type=qtypes[i%9],room='r%d'%i))+'\n' for i in range(400)))
        if withlogs:
            for n in ['launcher_chain.log','launcher_staging.log']+[f+'.hex' for f in fams]:
                (src/'logs'/n).write_bytes(b'line\n'*100000)
        rep = A.pack_partial(src, W/f'p_{tag}_{int(withlogs)}.tar.gz', cfg, 89900000-1)
        value = dict(schema='a3',token=cfg['token'],plan_sha256=cfg['plan_sha256'],job='1234567',returncode=1,synthetic=False,
            conflicting_terminal_markers=False,complete=False,status='PARTIAL',archive_complete=True,mode='production',partial=rep,
            archive=dict(name='result.tar.gz',bytes=12345678,sha256='a'*64),archive_bytes=12345678,archive_sha256='a'*64)
        print(tag, 'logs' if withlogs else 'nologs', 'EXIT.json bytes', len(json.dumps(value, indent=2, sort_keys=True)))
