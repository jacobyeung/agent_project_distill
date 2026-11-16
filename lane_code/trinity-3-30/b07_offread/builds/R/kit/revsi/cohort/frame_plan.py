"""Count decoded frames with the evaluator's sampler; packet counts are diagnostics."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reader/evaluator'))
from evalpath.sampling import sample_video
from media import frame_list
from evalpath.items import sha256


def one(path, packet_only=False):
    import av
    path=Path(path)
    with av.open(str(path)) as container:
        stream=container.streams.video[0]
        packets=sum(1 for p in container.demux(stream) if p.size>0)
        declared=stream.frames
    result=dict(packet_count=packets,container_frame_count=declared,sha256=sha256(path),
                packet_equals_decode=None,packet_count_is_authoritative=False)
    if packet_only:
        return result
    _,indices,fps,total=sample_video(dict(video_path=str(path)),SimpleNamespace(max_frames_num=32))
    expanded,_=frame_list(indices,fps,total,'duplicate')
    # These are the model's timing values. Retain actual PTS separately.
    with av.open(str(path)) as container:
        pts=[float(f.pts*f.time_base) for f in container.decode(video=0)]
    result.update(total_frames=total,fps=fps,anchor_indices=indices,duplicate_indices=expanded,
                  timestamps=[i/fps for i in expanded],anchor_timestamps=[i/fps for i in indices],
                  decoded_anchor_pts=[pts[i] for i in indices],packet_equals_decode=packets==total)
    return result


def source_timing(value,source):
    if value.get('total_frames')!=32:raise ValueError('Require exact tier-32 clip')
    total=source[-1]+1;fps=value['fps']*total/32
    expanded=[source[i] for i in value['duplicate_indices']]
    return dict(value,source_frame_indices=source,model_fps=fps,model_total_frames=total,
                model_duplicate_indices=expanded,model_timestamps=[i/fps for i in expanded])


def compute(directory,manifest,packet_only=False,selected=None,workers=16):
    rows=json.loads(Path(manifest).read_text())
    if selected is not None:rows=[r for r in rows if r['relative_path'] in set(selected)]
    indices=json.loads((Path(__file__).resolve().parents[1]/'inputs/i4.json').read_text())
    from concurrent.futures import ThreadPoolExecutor
    def inspect(r):
        path=Path(directory)/r['relative_path'] if directory else Path(r['alias_path'])
        value=one(path,packet_only)
        if value['sha256']!=r['sha256']:
            raise ValueError('Video SHA256 differs: '+r['relative_path'])
        if not packet_only and Path(r['relative_path']).stem in indices:
            value=source_timing(value,indices[Path(r['relative_path']).stem]['32-frame'])
        return r['relative_path'],value
    with ThreadPoolExecutor(max_workers=workers) as pool:
        result=dict(pool.map(inspect,rows))
    return dict(schema=1,mode='packets' if packet_only else 'decode',videos=result)


def check(tasks,cache,plan,index_sha):
    from media import frame_index,item_key,identity,cache_path
    expected=json.loads(Path(plan).read_text())
    if expected['mode']!='decode':raise ValueError('Packet counts cannot admit frame plans')
    index=frame_index(str(cache),index_sha)
    receipts={}
    for t in tasks:
        pin=index['items'][item_key(t,'duplicate')]
        if pin['path'] not in receipts:
            path=cache_path(cache,pin['path'])
            if sha256(path)!=pin['sha256']:raise ValueError('Frame receipt differs')
            receipts[pin['path']]=json.loads(path.read_text())
        receipt=receipts[pin['path']]
        if receipt['identity']!=identity(t,'duplicate'):raise ValueError('Frame identity differs')
        audit=receipt['audit']
        p=expected['videos'][t['scene']+'.mp4'] if t['benchmark']=='revsi' else expected['videos'][t['dataset']+'/'+t['scene_name']+'.mp4']
        if t['benchmark']=='revsi':
            if p['total_frames']!=32:raise ValueError('Require exact tier-32 clip')
            source=t['source_frame_indices'];total=source[-1]+1
            p=dict(p,duplicate_indices=[source[i] for i in p['duplicate_indices']],
                   total_frames=total,fps=p['fps']*total/32)
        if (audit['anchor_indices']!=p['anchor_indices'] or
            audit['metadata']['frames_indices']!=p['duplicate_indices'] or
            audit['metadata']['total_num_frames']!=p['total_frames'] or
            audit['metadata']['fps']!=p['fps']):
            raise ValueError('Realized frame plan differs: '+t['example_id'])
    return dict(items=len(tasks),videos=len(expected['videos']),pass_check=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--directory');p.add_argument('--manifest',default=str(Path(__file__).with_name('MEDIA_MANIFEST.json')))
    p.add_argument('--output',required=True);p.add_argument('--packet-only',action='store_true');p.add_argument('--video',action='append')
    a=p.parse_args();v=compute(a.directory,a.manifest,a.packet_only,a.video)
    Path(a.output).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(videos=len(v['videos']),mode=v['mode'],packet_decode_mismatches=[k for k,r in v['videos'].items() if r['packet_equals_decode'] is False])))
if __name__=='__main__':main()
