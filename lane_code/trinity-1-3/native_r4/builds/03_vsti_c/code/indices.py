"""Compare the prepared ordinals with a separately staged reference list."""
import argparse
from pathlib import Path
from adapter import load,checked,index_comparison,dump

def run(items,media,frames,selected,out):
    scenes=sorted({x['scene_name'] for x in load(items)})
    mapping=load(media);selections={}
    for scene in scenes:
        receipt=mapping['scannet:'+scene]['frame_receipt']
        path=Path(frames)/Path(receipt['path']).parent.name/'selection.json'
        checked(dict(path=str(path),sha256=receipt['sha256']))
        selections[scene]=load(path)['frame_indices']
    result=index_comparison(selections,selected);dump(out,result);return result

def main():
    p=argparse.ArgumentParser()
    for n in ('items','media','frames','selected','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();run(a.items,a.media,a.frames,a.selected,a.out)

if __name__=='__main__':main()
