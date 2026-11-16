"""Compare selected RGB pixels with a separately pinned video decode."""
import argparse
import math
from pathlib import Path
from adapter import checked,dump,load,pin,sha

SCENES=('scene0011_00','scene0077_01','scene0139_00','scene0334_02','scene0690_01')

def compare(video,selection,frames,expected_sha,required_av='17.1'):
    import av
    import numpy as np
    from PIL import Image
    if not av.__version__.startswith(required_av+'.') and av.__version__!=required_av:
        raise ValueError('decoder version differs: '+av.__version__)
    checked(dict(path=str(video),sha256=expected_sha));sel=load(selection)
    wanted={int(f['index']):f for f in sel['frames']};found={};count=0
    with av.open(str(video)) as container:
        stream=container.streams.video[0];stream.thread_count=1
        fps=float(stream.average_rate);declared=int(stream.frames)
        for count,frame in enumerate(container.decode(stream),1):
            index=count-1
            if index not in wanted:continue
            record=wanted[index];p=Path(frames)/Path(record['png']['path']).name
            checked(dict(path=str(p),sha256=record['png']['sha256']))
            a=frame.to_ndarray(format='rgb24');b=np.asarray(Image.open(p).convert('RGB'))
            if a.shape!=b.shape:raise ValueError('raster dimensions differ')
            delta=a.astype(np.float64)-b.astype(np.float64);mse=float(np.mean(delta*delta))
            found[index]=dict(index=index,max_absolute_difference=int(np.abs(delta).max()),
                mean_absolute_difference=float(np.abs(delta).mean()),psnr_db=10*math.log10(255**2/mse) if mse else None,
                psnr_infinite=mse==0,identical=mse==0)
    if set(found)!=set(wanted):raise ValueError('selected indices exceed decoded video')
    if count!=sel['total_num_frames']:raise ValueError('decoded frame count differs from selection')
    return dict(video=pin(video),selection=pin(selection),av=av.__version__,decoded_frames=count,declared_frames=declared,
                fps=fps,selected_frames=len(found),identical_frames=sum(x['identical'] for x in found.values()),
                frames=[found[i] for i in sorted(found)])

def run(videos,frames,media,pins,output):
    m=load(media);p=load(pins)['files'];records=[];missing=[]
    for scene in SCENES:
        video=Path(videos)/(scene+'.mp4');receipt=m['scannet:'+scene]['frame_receipt']
        folder=Path(frames)/Path(receipt['path']).parent.name;selection=folder/'selection.json'
        if not video.is_file() or not selection.is_file():missing.append(scene);continue
        checked(dict(path=str(selection),sha256=receipt['sha256']))
        records.append(dict(scene=scene,**compare(video,selection,folder,p[scene]['sha256'])))
    value=dict(schema='pixel-check-v1',status='complete' if not missing else 'pending',synthetic=False,
               missing=missing,records=records,identical_frames=sum(x['identical_frames'] for x in records),
               compared_frames=sum(x['selected_frames'] for x in records),pins=pin(pins))
    dump(output,value);return value

def main():
    p=argparse.ArgumentParser()
    for name in ('videos','frames','media','pins','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();run(a.videos,a.frames,a.media,a.pins,a.out)
if __name__=='__main__':main()
