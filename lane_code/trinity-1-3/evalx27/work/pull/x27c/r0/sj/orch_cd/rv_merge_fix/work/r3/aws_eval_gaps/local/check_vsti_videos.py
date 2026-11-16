"""Classify each local mirror video against the pinned release and known VSI encodes."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluator'))
from evalpath.items import sha256,VSTI_VIDEOS_SHA256

def check(root):
    inputs=Path(__file__).resolve().parents[1]/'inputs'
    release=inputs/'vsti_videos.json'
    if sha256(release)!=VSTI_VIDEOS_SHA256:raise ValueError('Release manifest changed')
    files=json.loads(release.read_text())['files']
    vsi=json.loads((inputs/'vsti_vsi_reencodes.json').read_text())['files']
    failed=False
    for scene,pin in sorted(files.items()):
        path=Path(root)/(scene+'.mp4');actual=sha256(path) if path.is_file() else None
        status=('RELEASE' if actual==pin['sha256'] else 'VSI_REENCODE' if actual and actual==vsi.get(scene) else 'OTHER_ENCODE' if actual else 'MISSING')
        print(scene,status,actual or '-',flush=True);failed |= status!='RELEASE'
    return int(failed)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mirror_video_directory')
    raise SystemExit(check(p.parse_args().mirror_video_directory))
