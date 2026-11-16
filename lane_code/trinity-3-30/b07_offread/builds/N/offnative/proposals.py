"""Run the pinned C8r proposal programs and bind their native cache receipts."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
import subprocess
import sys
from .c8 import install
from .io import dump, journal, load, sha, owned
from .staging import archive


def pin(path):
    return {'path':str(Path(path).resolve()),'sha256':sha(path)}


def frozen_programs(destination):
    P=install()
    P.frozen_kit.verify_local(P.KIT)
    archive(P.KIT/'kit_combo3.tar.gz',P.frozen_kit.ARCHIVE_SHA,destination,max_bytes=32*1024**2)
    root=Path(destination)/'kit_combo3/work'
    for name, expected in P.frozen_kit.CODE.items():
        if sha(root/name)!=expected:
            raise ValueError('frozen proposal program differs: '+name)
    return root


def build(captures, items, frames_root, destination, *, checkpoint, source, stub=False):
    """Captures contain 32 content-addressed RGB anchors and question-only names."""
    P=install()
    destination=owned(destination)
    if destination.exists():raise ValueError('proposal destination exists; no automatic retries')
    destination.mkdir(parents=True)
    code=frozen_programs(destination/'programs')
    kit,variants=P.cache_tools()
    # The module's files are byte-equal; WORK only resolves its frozen source inventory.
    old_work=variants.WORK
    variants.WORK=code
    try:
        provenance=destination/'items.jsonl'
        for item in items:journal(provenance,item)
        receipt=code/'vendor/SAM3_RECEIPT.json'
        base={'schema':'devs1-mask-manifest-v1','density':variants.BASE,
              'checkpoint_sha256':P.SAM_SHA,'receipt_sha256':sha(receipt),
              'items_sha256':sha(provenance),'captures':deepcopy(captures),
              'detect_calls':sum(len(c['phrases']) for c in captures),'test_stub':stub}
        if not captures:raise ValueError('proposal manifest needs captures')
        kit.validate_manifest(base)
        kit.check_prompt_provenance(base,items)
        if not stub and sha(checkpoint)!=P.SAM_SHA:
            raise ValueError('SAM 3 checkpoint differs')
        def execute(name, manifest, *extra):
            directory=destination/name
            directory.mkdir()
            mp=directory/'MANIFEST.json'; dump(mp,manifest)
            argv=[sys.executable,'-B',str(code/('cache_masks.py' if name=='baseline' else 'variant_cache.py')),
                  '--manifest',str(mp),'--frames',str(Path(frames_root).resolve()),
                  '--out',str(directory/'candidates'),'--receipt',str(receipt),
                  '--max-bytes','500000000','--max-seconds','14400']
            if stub:
                argv+=['--stub']
            else:argv+=['--checkpoint',str(checkpoint),'--source',str(source)]
            argv+=list(extra)
            with (directory/'execution.log').open('xb') as log:
                subprocess.run(argv,cwd=code,check=True,stdout=log,stderr=log)
            return directory/'candidates'
        baseline=execute('baseline',base)
        bp={c['scene']:sha(baseline/(c['scene'].replace('/','__')+'.npz')) for c in captures}
        dense_manifest=variants.make_manifest(base,'dense',sha(baseline.parent/'MANIFEST.json'),bp)
        dense=execute('dense',dense_manifest,'--baseline-cache',str(baseline))
        combined_manifest=variants.make_manifest(base,'dense_aliases',sha(baseline.parent/'MANIFEST.json'),bp,
                                                 dense=variants.dense_source(dense))
        combined=execute('dense_aliases',combined_manifest,'--baseline-cache',str(baseline),'--reuse-dense',str(dense))
        output=destination/'MASK_CACHE.json'
        if stub:
            # The production cache loader must continue rejecting CPU stub caches.
            for c in combined_manifest['captures']:
                p=combined/(c['scene'].replace('/','__')+'.npz')
                kit.validate_cache(kit.load_cache(p),c,sha(combined.parent/'MANIFEST.json'),allow_stub=True)
            dump(output,{'synthetic':True,'production_admissible':False,
                         'manifest':pin(combined.parent/'MANIFEST.json'),'candidates':str(combined)})
        else:
            import nomdg
            nomdg.cache_bind(NS(manifest=combined.parent/'MANIFEST.json',candidates=combined,
                                dense_candidates=dense,items=provenance,output=output))
            P.Masks(pin(output))
        return output
    finally:
        variants.WORK=old_work
