"""Pinned task adapters; media and labels never enter the prompt together."""
import json
from pathlib import Path
from evalpath.items import load_items, pinned, index_rows
from evalpath.kit_inputs import resolve_spec, official_rows, dev_rows
from evalpath.official import build_prompt_context

# sha256 of inputs/revsi999_rows_t{32,64}.json and revsi999_membership.json (local/build_revsi999.py, REVSI999_PROVENANCE.json).
REVSI999_ROWS = {32: '511c7e8a190235bd17b87a903db569abd5f6b245f444b50dfc3785c06f9be1e9',
                 64: '7597f52c4a3b104b795b072e5f7869eb45fd0c97f0db8c19a2132bbb410fec1e'}
# sha256 of inputs/revsi999_videos_t{32,64}.json (local/build_revsi999_videos.py over the landed official videos) (built 2026-11-11 from the landed official videos).
REVSI999_VIDEOS = {32: 'badb56dc5cd95118c686262ed9af4055d92727ae9e282b5a3b41198a96411c82',
                  64: '7e0adc9e98a59e4f20bcda6bbd4194e497a7e90b9b6c01f69826123aa525cf20'}
REVSI999_MEMBERSHIP = '03456abc2fcd8199ed4fb4a3af54651ed07df2e5a1efa752aa165006ad4b6850'


def tasks_for(spec, roots):
    if spec['benchmark'] == 'pointing_video':
        from pointing_video import tasks
        return tasks(spec,roots)
    if spec['benchmark'] == 'vsi500_slice':
        parent = {**spec, 'benchmark':'vsi500'}
        rows = load_items(parent, roots)
        selection = json.loads(pinned(spec['slice_membership']).read_text())
        members = {str(r['example_id']):r for r in selection['items']}
        if selection['seed'] != 17 or len(members) != 100 or len(selection['items']) != 100:
            raise ValueError('Require fixed 100-item seed-17 VSI slice')
        result = []
        for row in rows:
            if row['example_id'] not in members:continue
            m = members[row['example_id']]
            if (m['question_type'],m['scene'],m['dataset']) != (row['question_type'],row['scene_name'],row['dataset']):
                raise ValueError('VSI slice scene/type differs')
            result.append({**row,'benchmark':'vsi500_slice'})
        if len(result) != 100:raise ValueError('Missing VSI slice IDs')
        return result
    if spec['benchmark'] == 'pointing':
        value = json.loads(pinned(spec['membership']).read_text())
        rows = value['items']
        n=len(rows) if value.get('grounding') is True else 1000
        if len(rows)!=n or len({r['id'] for r in rows})!=n:
            raise ValueError('Pointing membership differs')
        return [dict(example_id=r['id'], benchmark='pointing', scene=r['scene'], scene_name=r['scene'],
                     question_type='point', point_prompt=value['contract']['prompt'].format(obj=r['obj']),
                     video_path=str(Path(roots['pointing_video_root'])/r['video_rel']),
                     frame=r['frame'], source_frame_indices=r['frame_indices'], source_index=r['source_index'],
                     fps=r['fps'], total_num_frames=r['total_num_frames']) for r in rows]
    if spec['benchmark'] == 'official5130':
        return official_rows(spec, roots)
    if spec['benchmark'] == 'devrows':
        return dev_rows(spec, roots)
    if spec['benchmark'] != 'revsi':
        return load_items(resolve_spec(spec, roots), roots)
    rows = json.loads(pinned(spec['rows']).read_text())
    members = json.loads(pinned(spec['membership']).read_text())
    revsi_set, tier = spec.get('set', 'cap452'), spec.get('tier', 32)
    expected = REVSI999_ROWS.get(tier) if revsi_set == 'official999' else (452 if tier == 32 else None)
    if expected is None:
        raise ValueError('ReVSI set/tier unsupported')
    if revsi_set == 'official999':
        if spec['rows']['sha256'] != expected or spec['membership']['sha256'] != REVSI999_MEMBERSHIP or spec.get('sidecar'):
            raise ValueError('ReVSI official999 rows differ from the parquet-built pins')
        expected = 999
        if not spec.get('videos') or REVSI999_VIDEOS.get(tier) is None or spec['videos']['sha256'] != REVSI999_VIDEOS[tier]:
            raise ValueError('ReVSI official999 requires the pinned per-tier video manifest')
        videos = json.loads(pinned(spec['videos']).read_text())
        if videos.get('tier') != tier or set(videos['files']) != {r['scene'] for r in rows}:
            raise ValueError('ReVSI video manifest tier or scenes differ')
    if len(rows) != expected or set(index_rows(rows)) != {m['qid'] for m in members}:
        raise ValueError('ReVSI membership differs')
    sidecar = None
    if spec.get('sidecar'):
        sidecar = json.loads(pinned(spec['sidecar']).read_text())
        if not spec['sidecar']['sha256'].startswith('66e0175d'):
            raise ValueError('Require the official 32-frame sidecar')
    indices = json.loads(pinned(spec['indices']).read_text())
    for row in rows:
        if sidecar is not None:
            gt = sidecar.get('revsi_'+row['example_id'], sidecar.get(row['example_id']))
            if gt is None or str(gt['ground_truth']) != str(row['ground_truth']):
                raise ValueError('ReVSI sidecar ground truth differs')
            if gt.get('leaf_type', gt.get('question_type')) != row['question_type']:
                raise ValueError('ReVSI sidecar question type differs')
        if str(row['num_frames']) != str(tier):
            raise ValueError('ReVSI row tier differs')
        row['source_frame_indices'] = indices[row['scene']][f'{tier}-frame']
        if len(row['source_frame_indices']) != tier:
            raise ValueError('ReVSI frame tier differs')
        row['revsi_tier'], row['revsi_set'] = tier, revsi_set
        row['video_path'] = str(Path(roots['revsi_video_root'])/(row['scene']+'.mp4'))
        if revsi_set == 'official999':
            row['video_sha256'] = videos['files'][row['scene']]['sha256']
        # Official999 GT is the official parquet itself (rows pinned above); cap452 still needs the 66e0175d sidecar.
        row['sidecar_verified'] = sidecar is not None or revsi_set == 'official999'
        build_prompt_context(row, 'ours')
    return sorted(rows, key=lambda x: x['example_id'])
