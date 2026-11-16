"""Resolve exact weight metadata from an offline HF API response supplied by staging."""
import argparse,json
from pathlib import Path

def resolve(payload):
    repo=payload['id'];rev=payload['sha']
    if len(rev)!=40:raise ValueError('Need immutable 40-character revision')
    result=[]
    for f in payload['siblings']:
        name=f['rfilename'];lfs=f.get('lfs') or {};size=f.get('size',lfs.get('size'))
        published=lfs.get('sha256') or lfs.get('oid','').removeprefix('sha256:')
        weight=name.endswith(('.safetensors','.pt','.bin'))
        if weight and (not isinstance(size,int) or len(published)!=64):raise ValueError('Missing exact published weight metadata: '+name)
        result.append(dict(url=f'https://huggingface.co/{repo}/resolve/{rev}/{name}',file=name,size=size,published_sha256=published or None,published_git_blob_sha1=f.get('blobId')))
    return dict(repo=repo,revision=rev,files=result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('metadata',nargs='+');p.add_argument('--out',required=True);a=p.parse_args()
    Path(a.out).write_text(json.dumps([resolve(json.loads(Path(f).read_text())) for f in a.metadata],indent=2)+'\n')
